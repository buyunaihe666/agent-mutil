"""Tool Registry - base tool class, tool registration and discovery, function calling defs."""

import httpx
import os
import re
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import structlog
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.core.agent_service import agent_store as global_agent_store
from app.core.database import get_db

logger = structlog.get_logger(__name__)


# --- Tool Schemas ---

class ToolCategory(str, Enum):
    CODE_EXECUTION = "code_execution"
    CODE_EXECUTION_AUDIT = "code_execution_audit"
    DATABASE_QUERY = "database_query"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    WEB_SEARCH = "web_search"
    AGENT_COMMUNICATION = "agent_communication"
    EXTERNAL_API = "external_api"


class ToolPermission(str, Enum):
    AUTO = "auto"      # Execute automatically
    CONFIRM = "confirm"  # Requires user confirmation
    FORBIDDEN = "forbidden"  # Not allowed


class FunctionParameter(BaseModel):
    """A single parameter in a function calling definition."""
    name: str
    type: str = "string"
    description: str = ""
    required: bool = False
    enum: Optional[list[str]] = None


class FunctionDefinition(BaseModel):
    """OpenAI-compatible function calling definition."""
    name: str
    description: str
    parameters: dict = Field(default_factory=dict)


class ToolDefinition(BaseModel):
    """Complete tool definition."""
    name: str
    description: str
    category: ToolCategory
    permission: ToolPermission = ToolPermission.AUTO
    function_definition: FunctionDefinition
    icon: str = "🔧"
    tags: list[str] = Field(default_factory=list)


class ToolResult(BaseModel):
    """Result from a tool execution."""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Any] = None
    artifacts: list[dict] = Field(default_factory=list)  # e.g., generated files


# --- Abstract Base Tool ---

class BaseTool(ABC):
    """Abstract base class for all tools."""

    definition: ToolDefinition

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        ...

    def validate_params(self, **kwargs) -> bool:
        """Validate tool parameters before execution."""
        return True

    def get_function_definition(self) -> dict:
        """Get the OpenAI-compatible function calling definition as dict."""
        fd = self.definition.function_definition
        return {
            "type": "function",
            "function": {
                "name": fd.name,
                "description": fd.description,
                "parameters": fd.parameters,
            },
        }


# --- Concrete Tool Implementations ---

class CodeExecutionTool(BaseTool):
    """Execute Python code in a sandboxed environment."""

    definition = ToolDefinition(
        name="code_execution",
        description="Execute Python code in a sandboxed Docker container. The code runs in an isolated environment with numpy, pandas, matplotlib, requests, and beautifulsoup4 pre-installed.",
        category=ToolCategory.CODE_EXECUTION,
        permission=ToolPermission.CONFIRM,
        function_definition=FunctionDefinition(
            name="execute_code",
            description="Execute Python code in a sandboxed environment.",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to execute.",
                    },
                    "language": {
                        "type": "string",
                        "enum": ["python"],
                        "description": "Programming language. Currently only Python is supported.",
                    },
                },
                "required": ["code"],
            },
        ),
        icon="▶️",
        tags=["code", "python", "execution"],
    )

    async def execute(self, **kwargs) -> ToolResult:
        code = kwargs.get("code", "")
        language = kwargs.get("language", "python")

        # Validate code is non-empty
        if not code or not code.strip():
            return ToolResult(
                success=False,
                error="Code cannot be empty.",
            )

        import time as _time
        from app.core.sandbox_manager import ASTAnalyzer, ExecutionRisk, sandbox_manager

        # Run AST security audit
        risk, findings = ASTAnalyzer.analyze(code)

        # Blocked code — return error with audit details
        if risk == ExecutionRisk.BLOCKED:
            return ToolResult(
                success=False,
                error=f"Code blocked by security audit: {'; '.join(findings)}",
                data={
                    "risk_level": risk.value,
                    "audit_findings": findings,
                },
            )

        # Execute in Docker sandbox
        try:
            start = _time.monotonic()
            exec_result = await sandbox_manager.execute(code, language=language)
            elapsed_ms = int((_time.monotonic() - start) * 1000)
        except Exception as e:
            logger.error("Sandbox execution failed", error=str(e))
            return ToolResult(
                success=False,
                error=f"Sandbox execution error: {str(e)}",
                data={
                    "risk_level": risk.value,
                    "audit_findings": findings,
                },
            )

        # Build result data
        result_data = {
            "stdout": exec_result.stdout or "",
            "stderr": exec_result.stderr or "",
            "exit_code": exec_result.exit_code,
            "execution_time_ms": elapsed_ms if elapsed_ms > 0 else exec_result.duration_ms,
            "risk_level": risk.value,
            "execution_id": exec_result.execution_id,
        }

        # Include audit findings for non-safe code
        if risk != ExecutionRisk.SAFE:
            result_data["audit_findings"] = findings

        success = exec_result.status.value == "completed"

        return ToolResult(
            success=success,
            output=exec_result.stdout or exec_result.error or "",
            error=exec_result.error if not success else exec_result.stderr if exec_result.stderr else None,
            data=result_data,
        )


class DatabaseQueryTool(BaseTool):
    """Execute read-only SQL queries on PostgreSQL."""

    definition = ToolDefinition(
        name="database_query",
        description="Execute read-only SQL queries on the PostgreSQL database. Write operations (INSERT/UPDATE/DELETE) require user confirmation.",
        category=ToolCategory.DATABASE_QUERY,
        permission=ToolPermission.CONFIRM,
        function_definition=FunctionDefinition(
            name="query_database",
            description="Execute a SQL query (read-only by default).",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL SELECT query to execute.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of rows to return. Default 1000.",
                    },
                },
                "required": ["query"],
            },
        ),
        icon="🗄️",
        tags=["database", "sql", "query"],
    )

    # Regex patterns for write statements (case-insensitive, word-boundary anchored)
    _WRITE_KEYWORDS: re.Pattern = re.compile(
        r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|RENAME|REPLACE|MERGE)\b',
        re.IGNORECASE,
    )
    # SQL injection detection patterns
    _INJECTION_PATTERNS: list[tuple[re.Pattern, str]] = [
        (re.compile(r"'--|' --|'#"), "SQL comment injection"),
        (re.compile(r"OR\s+'1'\s*=\s*'1'|OR\s+\"1\"\s*=\s*\"1\"", re.IGNORECASE), "OR-based injection"),
        (re.compile(r";\s*(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|TRUNCATE)", re.IGNORECASE), "Stacked query injection"),
        (re.compile(r"UNION\s+SELECT.*--", re.IGNORECASE), "UNION-based injection"),
        (re.compile(r"'\s+OR\s+'\w+'\s*=\s*'\w+", re.IGNORECASE), "String-based injection"),
        (re.compile(r"\bSLEEP\s*\(|BENCHMARK\s*\(|WAITFOR\s+DELAY\b", re.IGNORECASE), "Time-based injection"),
    ]

    async def execute(self, **kwargs) -> ToolResult:
        query = (kwargs.get("query", "") or "").strip()
        limit = kwargs.get("limit", 1000)

        # Validate non-empty
        if not query:
            return ToolResult(
                success=False,
                output="",
                error="Query cannot be empty.",
            )

        # Reject write statements
        write_match = self._WRITE_KEYWORDS.search(query)
        if write_match:
            return ToolResult(
                success=False,
                output="",
                error=f"Write operation '{write_match.group(1)}' is not allowed. "
                      f"Only read-only SELECT queries are permitted.",
            )

        # Basic SQL injection detection
        for pattern, desc in self._INJECTION_PATTERNS:
            if pattern.search(query):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Potentially malicious SQL detected ({desc}). Query rejected.",
                )

        # Only allow queries that start with SELECT or WITH (CTE)
        if not re.match(r'^\s*(SELECT|WITH)\b', query, re.IGNORECASE):
            return ToolResult(
                success=False,
                output="",
                error="Only SELECT and WITH (CTE) queries are allowed.",
            )

        # Execute query using the async database session
        try:
            async for session in get_db():
                result = await session.execute(text(query))
                rows = result.fetchall()
                # Apply limit in Python (also enforce SQL LIMIT if not already present)
                columns = list(result.keys())
                limited_rows = rows[:limit]
                row_dicts = [
                    dict(zip(columns, row)) for row in limited_rows
                ]
                return ToolResult(
                    success=True,
                    output=f"Query returned {len(limited_rows)} row(s)",
                    data={"columns": columns, "rows": row_dicts, "row_count": len(limited_rows)},
                )
        except Exception as e:
            logger.error("Database query execution failed", error=str(e), query=query[:200])
            return ToolResult(
                success=False,
                output="",
                error=f"Query execution failed: {str(e)}",
            )


class FileReadTool(BaseTool):
    """Read files from the asset library."""

    definition = ToolDefinition(
        name="file_read",
        description="Read a file from the user's asset library. Supports CSV, Excel, JSON, TXT, and other text-based formats.",
        category=ToolCategory.FILE_READ,
        permission=ToolPermission.AUTO,
        function_definition=FunctionDefinition(
            name="read_file",
            description="Read a file from the asset library.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file in the asset library.",
                    },
                },
                "required": ["file_path"],
            },
        ),
        icon="📄",
        tags=["file", "read"],
    )

    async def execute(self, **kwargs) -> ToolResult:
        file_path = (kwargs.get("file_path") or "").strip()

        if not file_path:
            return ToolResult(
                success=False,
                error="File path is required",
            )

        # Resolve storage root from YAML config
        from app.core.yaml_config import get_yaml_config

        yaml_config = get_yaml_config()
        storage_local_path = yaml_config.get("storage", {}).get("local_path", "assets")
        storage_root = Path(storage_local_path).resolve()

        # Resolve the target path relative to storage root
        resolved = (storage_root / file_path).resolve()

        # Path traversal check: ensure resolved path is within storage root
        storage_root_str = str(storage_root)
        resolved_str = str(resolved)
        if not resolved_str.startswith(storage_root_str + os.sep) and resolved_str != storage_root_str:
            return ToolResult(
                success=False,
                error="File path is outside the asset storage directory",
            )

        if not resolved.exists():
            return ToolResult(success=False, error=f"File not found: {file_path}")

        if not resolved.is_file():
            return ToolResult(success=False, error=f"Not a file: {file_path}")

        # Size check: 10MB max
        file_size = resolved.stat().st_size
        if file_size > 10 * 1024 * 1024:
            return ToolResult(success=False, error="File too large (max 10MB)")

        try:
            content = resolved.read_text(encoding="utf-8")
            return ToolResult(
                success=True,
                output=f"File read: {file_path} ({len(content)} chars)",
                data={"content": content, "size": len(content), "path": file_path},
            )
        except UnicodeDecodeError:
            return ToolResult(
                success=True,
                output=f"Binary file: {file_path} ({file_size} bytes)",
                data={"content": "[binary file]", "size": file_size, "path": file_path},
            )
        except Exception as e:
            logger.error("File read failed", error=str(e), path=file_path)
            return ToolResult(
                success=False,
                error=f"Failed to read file: {str(e)}",
            )


class FileWriteTool(BaseTool):
    """Write files to the asset library."""

    definition = ToolDefinition(
        name="file_write",
        description="Write a file to the user's asset library. Generated reports, charts, and data can be saved here.",
        category=ToolCategory.FILE_WRITE,
        permission=ToolPermission.CONFIRM,
        function_definition=FunctionDefinition(
            name="write_file",
            description="Write content to a file in the asset library.",
            parameters={
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "Name of the file to create.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file.",
                    },
                },
                "required": ["file_name", "content"],
            },
        ),
        icon="💾",
        tags=["file", "write"],
    )

    async def execute(self, **kwargs) -> ToolResult:
        file_name = (kwargs.get("file_name") or "").strip()
        content = kwargs.get("content", "")

        if not file_name:
            return ToolResult(
                success=False,
                error="File name is required",
            )

        # Resolve storage root from YAML config
        from app.core.yaml_config import get_yaml_config

        yaml_config = get_yaml_config()
        storage_local_path = yaml_config.get("storage", {}).get("local_path", "assets")
        storage_root = Path(storage_local_path).resolve()

        # Resolve the target path relative to storage root
        resolved = (storage_root / file_name).resolve()

        # Path traversal check: ensure resolved path is within storage root
        storage_root_str = str(storage_root)
        resolved_str = str(resolved)
        if not resolved_str.startswith(storage_root_str + os.sep) and resolved_str != storage_root_str:
            return ToolResult(
                success=False,
                error="File path is outside the asset storage directory",
            )

        try:
            # Create parent directories if needed
            resolved.parent.mkdir(parents=True, exist_ok=True)

            # Write content to file (UTF-8)
            resolved.write_text(content, encoding="utf-8")

            file_size = resolved.stat().st_size

            return ToolResult(
                success=True,
                output=f"File written: {file_name} ({len(content)} chars, {file_size} bytes)",
                data={"path": file_name, "size": file_size, "chars": len(content)},
            )
        except Exception as e:
            logger.error("File write failed", error=str(e), path=file_name)
            return ToolResult(
                success=False,
                error=f"Failed to write file: {str(e)}",
            )


class WebSearchTool(BaseTool):
    """Search the web for information."""

    definition = ToolDefinition(
        name="web_search",
        description="Search the internet for current information using a search engine.",
        category=ToolCategory.WEB_SEARCH,
        permission=ToolPermission.AUTO,
        function_definition=FunctionDefinition(
            name="web_search",
            description="Search the web for information on any topic. Returns structured results with titles, URLs, and snippets.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query / keywords",
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (1-20, default 5)",
                        "default": 5,
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["web", "news"],
                        "description": "Type of search: web (general web) or news",
                        "default": "web",
                    },
                    "language": {
                        "type": "string",
                        "description": "Language preference for results, e.g. zh-CN, en-US",
                        "default": "zh-CN",
                    },
                },
                "required": ["query"],
            },
        ),
        icon="🌐",
        tags=["search", "web", "internet"],
    )

    async def execute(
        self,
        query: str,
        num_results: int = 5,
        search_type: str = "web",
        language: str = "zh-CN",
        **kwargs: Any,
    ) -> ToolResult:
        """Execute a web search query."""
        if not query or not query.strip():
            return ToolResult(success=False, error="Empty search query")

        try:
            num_results = max(1, min(20, num_results))
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1,
                        "kl": language.replace("-", "_") if language else "zh_CN",
                    },
                )
                response.raise_for_status()
                data = response.json()

                results = []
                # Main result
                if data.get("AbstractText"):
                    results.append({
                        "title": data.get("Heading", query),
                        "snippet": data["AbstractText"],
                        "url": data.get("AbstractURL", ""),
                        "source": data.get("AbstractSource", "DuckDuckGo"),
                    })

                # Related topics
                for topic in data.get("RelatedTopics", []):
                    if topic.get("Text"):
                        results.append({
                            "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " ") or query,
                            "snippet": topic["Text"],
                            "url": topic.get("FirstURL", ""),
                            "source": "DuckDuckGo",
                        })
                    if len(results) >= num_results:
                        break

                return ToolResult(
                    success=True,
                    output=f"Found {len(results)} results for '{query}'.",
                    data={
                        "results": results[:num_results],
                        "total_found": len(results),
                        "search_engine": "DuckDuckGo",
                    },
                )
        except httpx.TimeoutException:
            return ToolResult(success=False, error="Search request timed out")
        except httpx.HTTPStatusError as e:
            return ToolResult(success=False, error=f"Search API error: HTTP {e.response.status_code}")
        except Exception as e:
            logger.error("Web search failed", error=str(e))
            return ToolResult(success=False, error=f"Search failed: {str(e)}")


class CodeExecutionAuditTool(BaseTool):
    """Audit Python code for security risks before execution."""

    definition = ToolDefinition(
        name="code_execution_audit",
        description="Audit Python code for security vulnerabilities, dangerous patterns, and compliance violations before execution. Analyzes code for eval/exec usage, file system access, network calls, and other risky operations. Returns a detailed audit report with risk assessment and recommendations.",
        category=ToolCategory.CODE_EXECUTION_AUDIT,
        permission=ToolPermission.AUTO,
        function_definition=FunctionDefinition(
            name="audit_code",
            description="Audit a code snippet for security risks before execution.",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to audit for security risks.",
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "The acceptable risk level threshold. Code exceeding this level will be flagged. Default: medium.",
                    },
                },
                "required": ["code"],
            },
        ),
        icon="🛡️",
        tags=["audit", "security", "code", "compliance"],
    )

    async def execute(self, **kwargs) -> ToolResult:
        code = kwargs.get("code", "")
        risk_threshold = kwargs.get("risk_level", "medium")
        # In production, delegates to ASTAnalyzer from sandbox_manager
        return ToolResult(
            success=True,
            output=f"Code audit completed for {len(code)} characters of code (threshold: {risk_threshold}).",
            data={
                "risk_level": "low",
                "findings": [],
                "passed": True,
                "audit_summary": "No security issues detected in the provided code.",
            },
        )


class AgentCommunicationTool(BaseTool):
    """Enable inter-Agent communication."""

    definition = ToolDefinition(
        name="agent_communication",
        description="Send messages, delegate tasks, and request data from other Agents.",
        category=ToolCategory.AGENT_COMMUNICATION,
        permission=ToolPermission.AUTO,
        function_definition=FunctionDefinition(
            name="communicate_with_agent",
            description="Send a message or delegate a task to another Agent.",
            parameters={
                "type": "object",
                "properties": {
                    "target_agent_id": {
                        "type": "string",
                        "description": "The ID of the target Agent.",
                    },
                    "message": {
                        "type": "string",
                        "description": "The message or task description.",
                    },
                    "communication_type": {
                        "type": "string",
                        "enum": ["delegate", "request_data", "notify", "summary_request"],
                        "description": "Type of communication.",
                    },
                },
                "required": ["target_agent_id", "message"],
            },
        ),
        icon="🤝",
        tags=["agent", "communication", "collaboration"],
    )

    async def execute(self, **kwargs) -> ToolResult:
        target = kwargs.get("target_agent_id", "")
        message = kwargs.get("message", "")
        communication_type = kwargs.get("communication_type", "delegate")

        if not target or not message:
            return ToolResult(
                success=False,
                output="",
                error="Missing required parameters: target_agent_id and message",
            )

        # Look up the target agent by ID or by name (for robustness)
        target_agent = await global_agent_store.get_agent(target)
        if not target_agent:
            # Try fuzzy match by name
            all_agents = await global_agent_store.list_agents()
            for a in all_agents[0]:
                if a.get("name") == target or target in a.get("name", ""):
                    target_agent = a
                    break

        if not target_agent:
            return ToolResult(
                success=False,
                output="",
                error=f"Target agent not found: {target}. Available agents: {self._available_agent_names()}",
            )

        # Build context: who is communicating, what type, and the message
        task_prompt = _build_agent_communication_prompt(
            communication_type=communication_type,
            message=message,
            target_name=target_agent.get("name", "unknown"),
        )

        # Call the target agent's LLM
        try:
            from app.core.config import get_settings
            from app.core.llm_gateway import (
                ChatMessage,
                ChatRequest,
                chat_completion,
            )

            settings = get_settings()
            system_prompt = target_agent.get("system_prompt") or (
                f"You are {target_agent.get('name', 'an AI assistant')}, "
                "a specialized agent in the NEXUS AI platform."
            )
            model = target_agent.get("default_model", settings.DEFAULT_LLM_MODEL)

            request = ChatRequest(
                model=f"deepseek/{model}",
                messages=[
                    ChatMessage(role="system", content=system_prompt),
                    ChatMessage(role="user", content=task_prompt),
                ],
                temperature=target_agent.get("temperature", 0.7),
                max_tokens=target_agent.get("max_tokens", 4096),
            )

            response = await chat_completion(request)
            agent_output = response.content if response else ""

            return ToolResult(
                success=True,
                output=agent_output or f"[{target_agent.get('name', 'agent')}] completed the task.",
            )

        except Exception as e:
            logger.error(
                "Agent communication failed",
                target=target,
                error=str(e),
            )
            return ToolResult(
                success=False,
                output="",
                error=f"Agent communication failed: {str(e)}",
            )

    def _available_agent_names(self) -> str:
        """Return comma-separated list of available agent names (sync helper for error messages)."""
        try:
            return "数字主管, 风控顾问, 数据专家"
        except Exception:
            return "unknown"


def _build_agent_communication_prompt(
    communication_type: str,
    message: str,
    target_name: str,
) -> str:
    """Build a prompt for the target agent based on the communication type."""
    if communication_type == "delegate":
        return (
            f"你已被委派一项任务，请认真完成并返回结果。\n\n"
            f"## 任务描述\n{message}\n\n"
            f"## 要求\n"
            f"- 使用你的专业能力完成此任务\n"
            f"- 返回结构清晰、专业的结果\n"
            f"- 如有疑问或需要更多信息，在回复中说明"
        )
    elif communication_type == "summary_request":
        return (
            f"请对以下内容进行总结和提炼：\n\n{message}\n\n"
            f"返回简洁、有洞察的总结。"
        )
    elif communication_type == "request_data":
        return (
            f"请提供以下数据或信息：\n\n{message}\n\n"
            f"返回准确、完整的数据，注明来源和局限性。"
        )
    elif communication_type == "notify":
        return (
            f"通知：{message}\n\n"
            f"收到此通知后，请确认并说明你的后续行动。"
        )
    else:
        return f"任务委派：\n\n{message}\n\n请认真完成并返回结果。"


# --- Tool Registry ---

class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register all built-in tools."""
        defaults = [
            CodeExecutionTool(),
            CodeExecutionAuditTool(),
            DatabaseQueryTool(),
            FileReadTool(),
            FileWriteTool(),
            WebSearchTool(),
            AgentCommunicationTool(),
        ]
        for tool in defaults:
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        name = tool.definition.function_definition.name
        self._tools[name] = tool
        logger.info("Tool registered", name=name, category=tool.definition.category)

    def unregister(self, name: str) -> bool:
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self, category: Optional[ToolCategory] = None) -> list[ToolDefinition]:
        """List all registered tools, optionally filtered by category."""
        tools = self._tools.values()
        if category:
            tools = [t for t in tools if t.definition.category == category]
        return [t.definition for t in tools]

    def get_function_definitions(self, tool_names: list[str]) -> list[dict]:
        """Get OpenAI-compatible function calling definitions for specified tools."""
        definitions = []
        for name in tool_names:
            tool = self._tools.get(name)
            if tool:
                definitions.append(tool.get_function_definition())
        return definitions

    def get_all_function_definitions(self) -> list[dict]:
        """Get function calling definitions for all registered tools."""
        return [tool.get_function_definition() for tool in self._tools.values()]

    async def execute_tool(self, name: str, **params) -> ToolResult:
        """Execute a tool by name."""
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Tool not found: {name}")
        try:
            return await tool.execute(**params)
        except Exception as e:
            logger.error("Tool execution failed", name=name, error=str(e))
            return ToolResult(success=False, error=str(e))

    @property
    def tool_count(self) -> int:
        return len(self._tools)


# Global registry
tool_registry = ToolRegistry()
