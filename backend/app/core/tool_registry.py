"""Tool Registry - base tool class, tool registration and discovery, function calling defs."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

import structlog
from pydantic import BaseModel, Field

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
        # Placeholder: actual Docker sandbox execution in M7
        return ToolResult(
            success=True,
            output=f"Code execution result for: {code[:50]}...",
            data={"stdout": "Execution simulated", "stderr": ""},
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

    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "")
        return ToolResult(
            success=True,
            output=f"Query executed: {query[:50]}...",
            data={"rows": [], "row_count": 0},
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
        file_path = kwargs.get("file_path", "")
        return ToolResult(
            success=True,
            output=f"File read: {file_path}",
            data={"content": "File content placeholder"},
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
        file_name = kwargs.get("file_name", "")
        return ToolResult(
            success=True,
            output=f"File written: {file_name}",
        )


class WebSearchTool(BaseTool):
    """Search the web for information."""

    definition = ToolDefinition(
        name="web_search",
        description="Search the internet for current information using a search engine.",
        category=ToolCategory.WEB_SEARCH,
        permission=ToolPermission.AUTO,
        function_definition=FunctionDefinition(
            name="search_web",
            description="Search the web for information.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return. Default 5.",
                    },
                },
                "required": ["query"],
            },
        ),
        icon="🌐",
        tags=["search", "web", "internet"],
    )

    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "")
        return ToolResult(
            success=True,
            output=f"Search results for: {query}",
            data={"results": []},
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
        return ToolResult(
            success=True,
            output=f"Message sent to agent {target}: {message[:50]}...",
        )


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
