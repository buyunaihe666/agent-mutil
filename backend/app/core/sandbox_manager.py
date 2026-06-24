"""Sandbox Manager - Docker container lifecycle, AST static code analysis."""

import ast
import asyncio
import io
import tarfile
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import structlog

from app.core.yaml_config import get_yaml_config

logger = structlog.get_logger(__name__)

yaml_config = get_yaml_config()
SANDBOX_CONFIG = yaml_config.get("sandbox", {})

SANDBOX_CONTAINER = SANDBOX_CONFIG.get("container_name", "nexus-sandbox")
SANDBOX_NETWORK = SANDBOX_CONFIG.get("network", "my-agent_default")
SANDBOX_TIMEOUT = SANDBOX_CONFIG.get("timeout", 60)

# --- Enums ---

class ExecutionRisk(str, Enum):
    SAFE = "safe"           # No dangerous operations detected
    WARNING = "warning"     # Potentially risky operations
    DANGEROUS = "dangerous" # Must confirm before execution
    BLOCKED = "blocked"     # Absolutely forbidden


class SandboxStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"


# --- AST Analyzer ---

class ASTAnalyzer:
    """Static code analysis using Python's ast module."""

    # Dangerous patterns that require user confirmation
    DANGEROUS_PATTERNS = {
        "os.system": "os.system() call",
        "subprocess.": "subprocess execution",
        "eval(": "eval() function call",
        "exec(": "exec() function call",
        "compile(": "compile() function call",
        "__import__(": "dynamic import",
        "importlib.": "importlib usage",
        "open(": "file open operation",
        "os.remove": "file deletion",
        "os.unlink": "file deletion",
        "shutil.rmtree": "directory deletion",
        "os.chmod": "file permission change",
        "socket.": "network socket operation",
        "requests.": "HTTP request",
        "urllib.": "URL operation",
    }

    # Absolutely forbidden patterns
    BLOCKED_PATTERNS = {
        "import pty": "PTY import - potential privilege escalation",
        "from pty import": "PTY import - potential privilege escalation",
        "os.setuid": "Privilege escalation attempt",
        "os.setgid": "Privilege escalation attempt",
        "ctypes.": "ctypes usage - can bypass Python security",
        "multiprocessing.": "Process spawning attempt",
    }

    @classmethod
    def analyze(cls, code: str) -> tuple[ExecutionRisk, list[str]]:
        """Analyze Python code and return risk level with findings.

        Returns:
            (risk_level, list of findings/warnings)
        """
        findings: list[str] = []
        risk = ExecutionRisk.SAFE

        # Check blocked patterns first (text-based)
        for pattern, description in cls.BLOCKED_PATTERNS.items():
            if pattern in code:
                findings.append(f"[BLOCKED] {description}")
                return ExecutionRisk.BLOCKED, findings

        # Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return ExecutionRisk.BLOCKED, [f"Syntax error: {e}"]

        # Check for dangerous patterns in AST
        walker = _ASTSecurityWalker(findings)
        walker.visit(tree)

        # Evaluate risk based on findings
        for finding in findings:
            if finding.startswith("[BLOCKED]"):
                risk = ExecutionRisk.BLOCKED
                break
            elif finding.startswith("[DANGEROUS]"):
                risk = ExecutionRisk.DANGEROUS
            elif finding.startswith("[WARNING]") and risk == ExecutionRisk.SAFE:
                risk = ExecutionRisk.WARNING

        return risk, findings


class _ASTSecurityWalker(ast.NodeVisitor):
    """Walk AST nodes to find security-relevant patterns."""

    def __init__(self, findings: list[str]):
        self.findings = findings

    def visit_Call(self, node):
        func_str = self._get_func_name(node)

        if any(dangerous in func_str for dangerous in [
            "os.system", "os.popen", "os.exec",
        ]):
            self.findings.append(f"[BLOCKED] Forbidden system call: {func_str}")
        elif "subprocess" in func_str:
            self.findings.append(f"[BLOCKED] Forbidden subprocess call: {func_str}")
        elif func_str in ("eval", "exec", "compile"):
            self.findings.append(f"[DANGEROUS] Dangerous function: {func_str}()")
        elif func_str == "__import__":
            self.findings.append("[DANGEROUS] Dynamic import detected")
        elif "open" in func_str:
            if node.args:
                first_arg = ast.dump(node.args[0])
                if any(sensitive in first_arg for sensitive in ["/etc", "/proc", "/sys", "~/.ssh"]):
                    self.findings.append("[DANGEROUS] Attempting to open sensitive path")
                else:
                    self.findings.append(f"[WARNING] File open: {func_str}")
        elif "socket" in func_str:
            self.findings.append(f"[WARNING] Socket operation: {func_str}")
        elif "requests" in func_str or "urllib" in func_str:
            self.findings.append(f"[WARNING] Network request: {func_str}")

        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in ("os", "subprocess", "ctypes", "multiprocessing"):
                self.findings.append(f"[WARNING] Import of potentially dangerous module: {alias.name}")
            if alias.name in ("pty",):
                self.findings.append(f"[BLOCKED] Forbidden import: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            full_name = f"{module}.{alias.name}"
            if any(blocked in full_name for blocked in ["os.setuid", "os.setgid", "subprocess", "ctypes"]):
                self.findings.append(f"[BLOCKED] Forbidden import: {full_name}")
        self.generic_visit(node)

    def _get_func_name(self, node) -> str:
        """Extract function name from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            obj = node.func
            while isinstance(obj, ast.Attribute):
                parts.append(obj.attr)
                obj = obj.value
            if isinstance(obj, ast.Name):
                parts.append(obj.id)
            return ".".join(reversed(parts))
        return "unknown"


# --- Sandbox Manager ---

@dataclass
class ExecutionResult:
    execution_id: str
    status: SandboxStatus
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    artifacts: list[dict] = None
    duration_ms: int = 0
    error: Optional[str] = None
    risk_level: Optional[str] = None
    findings: list[str] = None

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []
        if self.findings is None:
            self.findings = []


class SandboxManager:
    """Manages Docker sandbox containers for code execution.

    Executes user code inside the nexus-sandbox container via docker-py.
    Falls back to mock execution when Docker is unavailable.
    """

    def __init__(self):
        self._active_executions: dict[str, dict] = {}
        self.ast_analyzer = ASTAnalyzer()
        self._docker_client: Optional["docker.DockerClient"] = None
        self._docker_available: Optional[bool] = None

    @property
    def docker(self):
        """Lazy-initialized Docker client. Returns None if unavailable."""
        if self._docker_client is None and self._docker_available is not False:
            try:
                import docker as docker_mod
                self._docker_client = docker_mod.from_env()
                self._docker_client.ping()
                self._docker_available = True
                logger.info("Docker client connected")
            except Exception as e:
                self._docker_client = None
                self._docker_available = False
                logger.warning("Docker unavailable, sandbox will use mock execution",
                               error=str(e))
        return self._docker_client

    async def analyze_code(self, code: str) -> tuple[ExecutionRisk, list[str]]:
        """Perform AST security analysis on code."""
        return ASTAnalyzer.analyze(code)

    async def execute(
        self,
        code: str,
        language: str = "python",
        timeout: Optional[int] = None,
        env_vars: Optional[dict] = None,
        files: Optional[dict[str, str]] = None,
    ) -> ExecutionResult:
        """Execute code in a sandboxed Docker container.

        Steps:
        1. AST security audit
        2. If blocked → reject
        3. Copy code into the sandbox container
        4. Execute via `docker exec` inside the container
        5. Capture stdout/stderr/exit_code/elapsed time

        Falls back to mock execution if Docker is unavailable (dev/testing).
        """
        if timeout is None:
            timeout = SANDBOX_TIMEOUT

        execution_id = str(uuid.uuid4())

        # --- Step 1: AST audit ---
        risk, findings = await self.analyze_code(code)
        if risk == ExecutionRisk.BLOCKED:
            return ExecutionResult(
                execution_id=execution_id,
                status=SandboxStatus.ERROR,
                stderr="\n".join(findings),
                error="Code blocked by security analysis",
                risk_level=risk.value,
                findings=findings,
            )

        # --- Step 2: Try real Docker execution ---
        client = self.docker
        if client is not None:
            try:
                result = await self._execute_in_container(
                    client=client,
                    execution_id=execution_id,
                    code=code,
                    timeout=timeout,
                    risk=risk,
                    findings=findings,
                )
                self._active_executions[execution_id] = {
                    "result": result, "code": code, "risk": risk, "findings": findings,
                }
                return result
            except Exception as e:
                logger.warning(
                    "Docker sandbox execution failed, falling back to mock",
                    execution_id=execution_id,
                    error=str(e),
                )

        # --- Fallback: mock execution (tests / no Docker) ---
        return await self._execute_mock(
            execution_id=execution_id,
            code=code,
            language=language,
            timeout=timeout,
            risk=risk,
            findings=findings,
        )

    async def _execute_in_container(
        self,
        client: "docker.DockerClient",
        execution_id: str,
        code: str,
        timeout: int,
        risk: ExecutionRisk,
        findings: list[str],
    ) -> ExecutionResult:
        """Execute code for real inside the nexus-sandbox container."""
        loop = asyncio.get_event_loop()
        start = time.monotonic()

        # Ensure sandbox container is running
        try:
            container = client.containers.get(SANDBOX_CONTAINER)
        except Exception:
            return ExecutionResult(
                execution_id=execution_id,
                status=SandboxStatus.ERROR,
                error=f"Sandbox container '{SANDBOX_CONTAINER}' not found. "
                      "Run: docker compose up -d sandbox",
                risk_level=risk.value,
                findings=findings,
            )

        if container.status != "running":
            try:
                container.start()
            except Exception as e:
                return ExecutionResult(
                    execution_id=execution_id,
                    status=SandboxStatus.ERROR,
                    error=f"Failed to start sandbox container: {e}",
                    risk_level=risk.value,
                    findings=findings,
                )

        # Write code to a temp file inside the container via tar archive
        script_path = "/workspace"
        script_name = f"_nexus_{execution_id[:8]}.py"
        container_path = f"{script_path}/{script_name}"

        tar_stream = io.BytesIO()
        tf = tarfile.TarFile(fileobj=tar_stream, mode="w")
        code_bytes = (code + "\n").encode("utf-8")
        info = tarfile.TarInfo(name=script_name)
        info.size = len(code_bytes)
        info.mode = 0o644
        tf.addfile(info, io.BytesIO(code_bytes))
        tf.close()
        tar_stream.seek(0)

        try:
            container.put_archive(script_path, tar_stream)
        except Exception as e:
            return ExecutionResult(
                execution_id=execution_id,
                status=SandboxStatus.ERROR,
                error=f"Failed to upload code to sandbox: {e}",
                risk_level=risk.value,
                findings=findings,
            )

        # Execute the script inside the container
        exec_cmd = ["python", container_path]
        try:
            exit_code, stdout = await loop.run_in_executor(
                None,
                lambda: container.exec_run(
                    cmd=exec_cmd,
                    user="sandbox",
                    workdir="/workspace",
                    environment={
                        "PYTHONUNBUFFERED": "1",
                        "NEXUS_EXECUTION_ID": execution_id,
                    },
                ),
            )
            # exec_run returns (exit_code, output) — output is bytes
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            stderr = ""  # exec_run combines stdout+stderr in the output
        except Exception as e:
            elapsed = int((time.monotonic() - start) * 1000)
            return ExecutionResult(
                execution_id=execution_id,
                status=SandboxStatus.ERROR,
                error=f"Sandbox execution failed: {e}",
                duration_ms=elapsed,
                risk_level=risk.value,
                findings=findings,
            )

        # Cleanup the temp file
        try:
            container.exec_run(cmd=["rm", "-f", script_name], workdir="/workspace")
        except Exception:
            pass

        elapsed = int((time.monotonic() - start) * 1000)

        if exit_code is None:
            exit_code = -1

        status = SandboxStatus.COMPLETED if exit_code == 0 else SandboxStatus.ERROR

        result = ExecutionResult(
            execution_id=execution_id,
            status=status,
            stdout=stdout or "",
            stderr=stderr or "",
            exit_code=exit_code,
            duration_ms=elapsed,
            risk_level=risk.value,
            findings=findings,
        )

        self._active_executions[execution_id] = {
            "result": result,
            "code": code,
            "risk": risk,
            "findings": findings,
        }

        return result

    async def _execute_mock(
        self,
        execution_id: str,
        code: str,
        language: str,
        timeout: int,
        risk: ExecutionRisk,
        findings: list[str],
    ) -> ExecutionResult:
        """Mock execution for development/testing when Docker is unavailable."""
        logger.info(
            "Mock sandbox execution",
            execution_id=execution_id,
            code_length=len(code),
            language=language,
            risk=risk,
        )

        result = ExecutionResult(
            execution_id=execution_id,
            status=SandboxStatus.COMPLETED,
            stdout=(
                f"[sandbox mock] Executed {len(code)} chars of {language} code.\n"
                f"Risk: {risk.value}\n"
                f"Docker not available — run 'docker compose up -d sandbox' for real execution."
            ),
            stderr="",
            exit_code=0,
            duration_ms=0,
            risk_level=risk.value,
            findings=findings,
        )

        self._active_executions[execution_id] = {
            "result": result,
            "code": code,
            "risk": risk,
            "findings": findings,
        }

        return result

    async def get_execution(self, execution_id: str) -> Optional[dict]:
        """Get execution details by ID."""
        return self._active_executions.get(execution_id)

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        if execution_id in self._active_executions:
            self._active_executions[execution_id]["result"].status = SandboxStatus.ERROR
            self._active_executions[execution_id]["result"].error = "Cancelled by user"
            return True
        return False

    def get_active_count(self) -> int:
        """Get count of active executions."""
        return len([e for e in self._active_executions.values()
                    if e["result"].status == SandboxStatus.RUNNING])

    def get_sandbox_info(self) -> dict:
        """Get sandbox configuration info."""
        return {
            "container_name": SANDBOX_CONTAINER,
            "network": SANDBOX_NETWORK,
            "memory_limit": SANDBOX_CONFIG.get("memory_limit", "512m"),
            "cpu_limit": SANDBOX_CONFIG.get("cpu_limit", 1.0),
            "timeout": SANDBOX_TIMEOUT,
            "network_enabled": SANDBOX_CONFIG.get("network_enabled", True),
            "preinstalled_libs": SANDBOX_CONFIG.get("preinstalled_libs", []),
            "active_executions": self.get_active_count(),
            "docker_available": self._docker_available,
        }


# Global instance
sandbox_manager = SandboxManager()
