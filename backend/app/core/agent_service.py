"""Agent Service - Agent CRUD, version management, templates, persona."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# --- Schemas ---

class PermissionLevel(int, Enum):
    L1_READ = 1
    L2_ANALYZE = 2
    L3_OPERATE = 3
    L4_ADMIN = 4


class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    avatar_emoji: Optional[str] = Field(None, max_length=10)
    system_prompt: Optional[str] = None
    tools: Optional[list[str]] = None
    default_model: str = "deepseek-chat"
    permission_level: int = 1
    temperature: float = Field(0.7, ge=0, le=2.0)
    max_tokens: int = Field(4096, gt=0)
    timeout_seconds: int = Field(300, gt=0)
    config: Optional[dict] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_emoji: Optional[str] = None
    system_prompt: Optional[str] = None
    tools: Optional[list[str]] = None
    default_model: Optional[str] = None
    permission_level: Optional[int] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout_seconds: Optional[int] = None
    is_active: Optional[bool] = None
    config: Optional[dict] = None


class AgentSummary(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    avatar_emoji: Optional[str] = None
    permission_level: int = 1
    is_preset: bool = False
    is_active: bool = True
    tools: Optional[list[str]] = None
    created_at: str
    updated_at: str


class AgentDetail(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    avatar_emoji: Optional[str] = None
    system_prompt: Optional[str] = None
    tools: Optional[list[str]] = None
    default_model: str
    permission_level: int
    temperature: float
    max_tokens: int
    timeout_seconds: int
    is_preset: bool = False
    is_active: bool = True
    config: Optional[dict] = None
    version_count: int = 0
    created_at: str
    updated_at: str


class AgentVersionDetail(BaseModel):
    id: str
    agent_id: str
    version_number: int
    system_prompt: Optional[str] = None
    tools: Optional[list[str]] = None
    config: Optional[dict] = None
    change_description: Optional[str] = None
    created_at: str


class AgentTemplate(BaseModel):
    id: str
    name: str
    description: str
    category: str
    avatar_emoji: str
    system_prompt: str
    tools: list[str]
    recommended_model: str = "deepseek-chat"


# --- Preset Agent Templates ---

PRESET_TEMPLATES: list[AgentTemplate] = [
    AgentTemplate(
        id="template-market-analysis",
        name="市场分析",
        description="分析市场趋势、竞品动态、行业报告",
        category="分析",
        avatar_emoji="📈",
        system_prompt="你是一个市场分析专家，擅长分析市场趋势、竞品动态和行业报告。请用数据和事实说话，提供可操作的洞察。",
        tools=["web_search", "file_read", "code_execution"],
        recommended_model="deepseek-chat",
    ),
    AgentTemplate(
        id="template-code-review",
        name="代码审查",
        description="审查代码质量、安全漏洞、性能优化",
        category="开发",
        avatar_emoji="🔍",
        system_prompt="你是一个资深代码审查专家，负责检查代码的质量、安全性、性能和可维护性。请给出具体、可操作的改进建议。",
        tools=["code_execution", "file_read"],
        recommended_model="deepseek-coder",
    ),
    AgentTemplate(
        id="template-document-writer",
        name="文档撰写",
        description="撰写技术文档、报告、方案",
        category="内容",
        avatar_emoji="✍️",
        system_prompt="你是一个专业的技术文档撰写者，擅长将复杂概念转化为清晰、结构化的文档。请使用 Markdown 格式输出。",
        tools=["file_read", "file_write"],
        recommended_model="deepseek-chat",
    ),
    AgentTemplate(
        id="template-data-analysis",
        name="数据分析",
        description="SQL查询、数据清洗、统计分析、图表生成",
        category="分析",
        avatar_emoji="📊",
        system_prompt="你是一个数据分析师，擅长SQL查询、数据清洗、统计分析和可视化。请为你的每个分析结论提供数据支持。",
        tools=["database_query", "code_execution", "file_read", "file_write"],
        recommended_model="deepseek-chat",
    ),
    AgentTemplate(
        id="template-security-audit",
        name="安全审计",
        description="系统安全审计、漏洞扫描、合规检查",
        category="安全",
        avatar_emoji="🛡️",
        system_prompt="你是一个安全审计专家，负责检查系统的安全性、合规性和潜在漏洞。请谨慎、严谨地评估每一项风险。",
        tools=["code_execution_audit", "file_read", "database_query"],
        recommended_model="deepseek-chat",
    ),
]

PRESET_AGENTS = [
    {
        "name": "数字主管",
        "description": "任务拆解与分配协调者",
        "avatar_emoji": "🎯",
        "system_prompt": "你是一个数字主管，负责分析用户任务、拆解为子任务、分配给合适的Worker Agent。你需要从全局视角思考，确保任务完整覆盖。",
        "tools": ["file_read", "agent_communication"],
        "default_model": "deepseek-chat",
        "permission_level": 4,
        "temperature": 0.3,
        "max_tokens": 8192,
        "timeout_seconds": 600,
        "is_preset": True,
        "is_active": True,
    },
    {
        "name": "风控顾问",
        "description": "安全审计与合规检查",
        "avatar_emoji": "🛡️",
        "system_prompt": "你是一个风控顾问，负责监控系统操作、检测未授权访问、审计代码执行、检查数据合规。你的语气谨慎、严谨、合规导向。",
        "tools": ["code_execution_audit", "file_read", "database_query"],
        "default_model": "deepseek-chat",
        "permission_level": 3,
        "temperature": 0.2,
        "max_tokens": 8192,
        "timeout_seconds": 300,
        "is_preset": True,
        "is_active": True,
    },
    {
        "name": "数据专家",
        "description": "数据处理与分析",
        "avatar_emoji": "📊",
        "system_prompt": "你是一个数据专家，擅长SQL查询、数据清洗、统计分析和图表生成。你的回答技术化、精确、数据导向。",
        "tools": ["database_query", "code_execution", "file_read", "web_search"],
        "default_model": "deepseek-chat",
        "permission_level": 2,
        "temperature": 0.4,
        "max_tokens": 8192,
        "timeout_seconds": 300,
        "is_preset": True,
        "is_active": True,
    },
]


# --- Agent Store (in-memory, mock for testing) ---

class AgentStore:
    """In-memory agent store. Will be replaced with DB-backed Repository."""

    def __init__(self):
        self.agents: dict[str, dict] = {}
        self.versions: dict[str, list[dict]] = {}  # agent_id -> [versions]
        self._init_presets()

    def _init_presets(self):
        """Initialize preset agents."""
        for preset in PRESET_AGENTS:
            agent_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"preset:{preset['name']}"))
            now = datetime.now(timezone.utc).isoformat()
            self.agents[agent_id] = {
                "id": agent_id,
                **preset,
                "config": None,
                "created_at": now,
                "updated_at": now,
            }
            # Create initial version
            self.versions[agent_id] = [{
                "id": str(uuid.uuid4()),
                "agent_id": agent_id,
                "version_number": 1,
                "system_prompt": preset["system_prompt"],
                "tools": preset["tools"],
                "config": None,
                "change_description": "Initial preset version",
                "created_at": now,
            }]

    async def list_agents(
        self,
        search: Optional[str] = None,
        permission_level: Optional[int] = None,
        is_active: Optional[bool] = None,
        tools: Optional[list[str]] = None,
        sort_by: str = "updated_at",
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        results = list(self.agents.values())

        if search:
            results = [a for a in results if search.lower() in a["name"].lower() or (a.get("description") and search.lower() in a["description"].lower())]
        if permission_level is not None:
            results = [a for a in results if a["permission_level"] == permission_level]
        if is_active is not None:
            results = [a for a in results if a["is_active"] == is_active]
        if tools:
            results = [a for a in results if all(t in (a.get("tools") or []) for t in tools)]

        results.sort(key=lambda a: a.get(sort_by, ""), reverse=True)
        total = len(results)
        return results[offset : offset + limit], total

    async def create_agent(self, data: AgentCreate) -> dict:
        agent_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        agent = {
            "id": agent_id,
            "name": data.name,
            "description": data.description,
            "avatar_emoji": data.avatar_emoji,
            "system_prompt": data.system_prompt,
            "tools": data.tools or [],
            "default_model": data.default_model,
            "permission_level": data.permission_level,
            "temperature": data.temperature,
            "max_tokens": data.max_tokens,
            "timeout_seconds": data.timeout_seconds,
            "is_preset": False,
            "is_active": True,
            "config": data.config,
            "created_at": now,
            "updated_at": now,
        }
        self.agents[agent_id] = agent
        self.versions[agent_id] = [{
            "id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "version_number": 1,
            "system_prompt": data.system_prompt,
            "tools": data.tools or [],
            "config": data.config,
            "change_description": "Initial version",
            "created_at": now,
        }]
        return agent

    async def get_agent(self, agent_id: str) -> Optional[dict]:
        return self.agents.get(agent_id)

    async def update_agent(self, agent_id: str, data: AgentUpdate) -> Optional[dict]:
        agent = self.agents.get(agent_id)
        if not agent:
            return None

        changed = False
        for field in ["name", "description", "avatar_emoji", "system_prompt", "default_model",
                       "temperature", "max_tokens", "timeout_seconds", "is_active", "config"]:
            val = getattr(data, field, None)
            if val is not None:
                agent[field] = val
                changed = True
        if data.tools is not None:
            agent["tools"] = data.tools
            changed = True
        if data.permission_level is not None:
            agent["permission_level"] = data.permission_level
            changed = True

        if changed:
            agent["updated_at"] = datetime.now(timezone.utc).isoformat()
            # Create new version if system_prompt or tools changed
            if data.system_prompt is not None or data.tools is not None:
                await self._save_version(agent_id, data)

        return agent

    async def delete_agent(self, agent_id: str) -> bool:
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        if agent.get("is_preset"):
            raise ValueError("Preset agents cannot be deleted")
        del self.agents[agent_id]
        self.versions.pop(agent_id, None)
        return True

    async def _save_version(self, agent_id: str, data: AgentUpdate) -> dict:
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError("Agent not found")
        latest = self.versions.get(agent_id, [])
        next_version = len(latest) + 1
        now = datetime.now(timezone.utc).isoformat()
        version = {
            "id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "version_number": next_version,
            "system_prompt": agent["system_prompt"],
            "tools": agent["tools"],
            "config": agent.get("config"),
            "change_description": "Configuration updated",
            "created_at": now,
        }
        self.versions.setdefault(agent_id, []).append(version)
        return version

    async def get_versions(self, agent_id: str) -> list[dict]:
        return self.versions.get(agent_id, [])

    async def get_version(self, agent_id: str, version_number: int) -> Optional[dict]:
        versions = self.versions.get(agent_id, [])
        for v in versions:
            if v["version_number"] == version_number:
                return v
        return None

    async def rollback_version(self, agent_id: str, version_number: int) -> Optional[dict]:
        target = await self.get_version(agent_id, version_number)
        if not target:
            return None
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        agent["system_prompt"] = target["system_prompt"]
        agent["tools"] = target["tools"]
        if target.get("config"):
            agent["config"] = target["config"]
        agent["updated_at"] = datetime.now(timezone.utc).isoformat()
        return agent

    def get_templates(self) -> list[AgentTemplate]:
        return PRESET_TEMPLATES

    def get_template(self, template_id: str) -> Optional[AgentTemplate]:
        for t in PRESET_TEMPLATES:
            if t.id == template_id:
                return t
        return None


# Global store
agent_store = AgentStore()
