"""Sandbox Manager - Docker container lifecycle, AST static code analysis."""

import ast
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import structlog

from app.core.yaml_config import get_yaml_config

logger = structlog.get_logger(__name__)

yaml_config = get_yaml_config()
SANDBOX_CONFIG = yaml_config.get("sandbox", {})


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
        self._in_functiondef = False

    def visit_Call(self, node):
        func_str = self._get_func_name(node)

        # Check for dangerous calls
        if any(dangerous in func_str for dangerous in [
            "os.system", "os.popen", "os.exec",
        ]):
            self.findings.append(f"[BLOCKED] Forbidden system call: {func_str}")
        elif "subprocess" in func_str:
            self.findings.append(f"[BLOCKED] Forbidden subprocess call: {func_str}")
        elif func_str in ("eval", "exec", "compile"):
            self.findings.append(f"[DANGEROUS] Dangerous function: {func_str}()")
        elif func_str == "__import__":
            self.findings.append(f"[DANGEROUS] Dynamic import detected")
        elif "open" in func_str:
            # Check if opening a sensitive path
            if node.args:
                first_arg = ast.dump(node.args[0])
                if any(sensitive in first_arg for sensitive in ["/etc", "/proc", "/sys", "~/.ssh"]):
                    self.findings.append(f"[DANGEROUS] Attempting to open sensitive path")
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

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


class SandboxManager:
    """Manages Docker sandbox containers for code execution."""

    def __init__(self):
        self._active_executions: dict[str, dict] = {}
        self.ast_analyzer = ASTAnalyzer()

    async def analyze_code(self, code: str) -> tuple[ExecutionRisk, list[str]]:
        """Perform AST security analysis on code."""
        return ASTAnalyzer.analyze(code)

    async def execute(
        self,
        code: str,
        language: str = "python",
        timeout: Optional[int] = None,
        env_vars: Optional[dict] = None,
        files: Optional[dict[str, str]] = None,  # filename -> content mapping
    ) -> ExecutionResult:
        """Execute code in a sandboxed Docker container.

        Note: This is a mock implementation for testing.
        Real Docker execution via docker-py goes live with Docker daemon available.
        """
        if timeout is None:
            timeout = SANDBOX_CONFIG.get("timeout", 60)

        execution_id = str(uuid.uuid4())

        # AST analysis
        risk, findings = await self.analyze_code(code)
        if risk == ExecutionRisk.BLOCKED:
            return ExecutionResult(
                execution_id=execution_id,
                status=SandboxStatus.ERROR,
                stderr="\n".join(findings),
                error="Code blocked by security analysis",
            )

        # Mock execution result
        logger.info(
            "Executing code in sandbox",
            execution_id=execution_id,
            code_length=len(code),
            language=language,
            risk=risk,
        )

        # Simulate execution
        result = ExecutionResult(
            execution_id=execution_id,
            status=SandboxStatus.COMPLETED,
            stdout=f"Mock execution output for {len(code)} chars of {language} code",
            stderr="",
            exit_code=0,
            duration_ms=150,
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
            "memory_limit": SANDBOX_CONFIG.get("memory_limit", "512m"),
            "cpu_limit": SANDBOX_CONFIG.get("cpu_limit", 1.0),
            "timeout": SANDBOX_CONFIG.get("timeout", 60),
            "network_enabled": SANDBOX_CONFIG.get("network_enabled", True),
            "preinstalled_libs": SANDBOX_CONFIG.get("preinstalled_libs", []),
            "active_executions": self.get_active_count(),
        }


# Global instance
sandbox_manager = SandboxManager()
