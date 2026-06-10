"""Tests for health check endpoint and app configuration."""

import pytest
from httpx import AsyncClient

from app.core.config import Settings, get_settings
from app.core.yaml_config import get_yaml_config, load_yaml_config
from app.core.security import (
    PermissionLevel,
    AuditLogger,
    RateLimiter,
    desensitize,
)
from app.core.ws import ConnectionManager, MessageType, ServerMessage, ClientMessage


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]


@pytest.mark.asyncio
async def test_health_endpoint_content_type(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.headers["content-type"].startswith("application/json")


@pytest.mark.asyncio
async def test_app_title(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200


# --- Config Tests (M12) ---

def test_settings_loads_with_defaults():
    s = Settings()
    assert s.APP_ENV == "development"
    assert s.DATABASE_URL is not None
    assert s.CORS_ORIGINS is not None


def test_settings_parses_api_keys():
    s = Settings(LLM_API_KEYS='{"deepseek":"sk-test123"}')
    key = s.get_api_key("deepseek")
    assert key == "sk-test123"


def test_settings_parses_cors_list():
    s = Settings(CORS_ORIGINS=["http://localhost:3000"])
    origins = s.CORS_ORIGINS
    assert "http://localhost:3000" in origins


def test_settings_parses_cors_string():
    s = Settings(CORS_ORIGINS="http://a.com,http://b.com")
    origins = s.CORS_ORIGINS
    assert "http://a.com" in origins
    assert "http://b.com" in origins


def test_yaml_config_loads_defaults():
    config = load_yaml_config()
    assert "models" in config
    assert "agents" in config
    assert "sandbox" in config
    assert "security" in config


def test_yaml_config_has_preset_agents():
    config = load_yaml_config()
    presets = config["agents"]["presets"]
    assert len(presets) == 3
    names = [a["name"] for a in presets]
    assert "数字主管" in names
    assert "风控顾问" in names
    assert "数据专家" in names


def test_yaml_config_has_model_providers():
    config = load_yaml_config()
    providers = config["models"]["providers"]
    assert len(providers) >= 3


# --- WebSocket Tests (M11) ---

def test_client_message_schema():
    msg = ClientMessage(type=MessageType.USER_MESSAGE, content="hello")
    assert msg.type == MessageType.USER_MESSAGE
    assert msg.content == "hello"


def test_server_message_schema():
    msg = ServerMessage(type=MessageType.SYSTEM, content="test message")
    assert msg.type == MessageType.SYSTEM
    assert msg.content == "test message"
    assert msg.message_id is not None


def test_server_message_json_serialization():
    msg = ServerMessage(type=MessageType.PONG, conversation_id="conv-123")
    json_str = msg.model_dump_json()
    assert "pong" in json_str.lower() or "PONG" in json_str
    assert "conv-123" in json_str


def test_connection_manager_init():
    manager = ConnectionManager()
    assert manager.chat_connection_count == 0
    assert manager.monitor_connection_count == 0
    assert manager.agent_connection_count == 0


def test_connection_manager_stats():
    manager = ConnectionManager()
    stats = manager.get_stats()
    assert stats["chat_connections"] == 0
    assert stats["monitor_connections"] == 0


# --- Security Tests (M9) ---

def test_permission_levels():
    assert PermissionLevel.READ_ONLY == 1
    assert PermissionLevel.ANALYZE == 2
    assert PermissionLevel.OPERATE == 3
    assert PermissionLevel.ADMIN == 4


def test_audit_logger_log_and_query():
    logger = AuditLogger()
    logger.clear()
    logger.log("test_action", resource_type="agent", user_id="user-1")
    results = logger.query(action_type="test_action")
    assert len(results) == 1
    assert results[0]["action_type"] == "test_action"
    logger.clear()


def test_audit_logger_filter_by_user():
    logger = AuditLogger()
    logger.clear()
    logger.log("action_a", user_id="user-1")
    logger.log("action_b", user_id="user-2")
    results = logger.query(user_id="user-1")
    assert len(results) == 1
    assert results[0]["user_id"] == "user-1"
    logger.clear()


def test_desensitize_phone():
    result = desensitize("Call 13812345678 for info")
    assert "13812345678" not in result
    assert "****-PHONE" in result


def test_desensitize_email():
    result = desensitize("Email test@example.com")
    assert "test@example.com" not in result
    assert "****-EMAIL" in result


def test_desensitize_card():
    result = desensitize("Card: 1234567890123456")
    assert "1234567890123456" not in result
    assert "****-CARD" in result


def test_rate_limiter_allows_within_limit():
    limiter = RateLimiter()
    limiter.clear()
    for _ in range(5):
        assert limiter.check("test-key", 10) is True


def test_rate_limiter_blocks_exceeded():
    limiter = RateLimiter()
    limiter.clear()
    for _ in range(3):
        limiter.check("block-key", 3)
    assert limiter.check("block-key", 3) is False


def test_rate_limiter_remaining():
    limiter = RateLimiter()
    limiter.clear()
    limiter.check("rem-key", 10)
    remaining = limiter.remaining("rem-key", 10)
    assert remaining == 9
    limiter.clear()


def test_rate_limiter_different_keys_independent():
    limiter = RateLimiter()
    limiter.clear()
    for _ in range(5):
        limiter.check("key-a", 5)
    assert limiter.check("key-a", 5) is False
    assert limiter.check("key-b", 5) is True
    limiter.clear()


# --- LLM Gateway Tests (M1) ---

from app.core.llm_gateway import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    Delta,
    ModelInfo,
    get_available_models,
    _get_model_timeout,
)


def test_get_available_models_returns_list():
    models = get_available_models()
    assert isinstance(models, list)
    assert len(models) > 0
    assert all(isinstance(m, ModelInfo) for m in models)


def test_get_available_models_has_deepseek():
    models = get_available_models()
    model_ids = [m.id for m in models]
    assert "deepseek-chat" in model_ids


def test_model_timeout_deepseek():
    timeout = _get_model_timeout("deepseek-chat")
    assert timeout == 120


def test_model_timeout_claude():
    timeout = _get_model_timeout("claude-sonnet-4-6")
    assert timeout == 180


def test_chat_message_to_dict():
    msg = ChatMessage(role="user", content="Hello")
    d = msg.__dict__
    assert d["role"] == "user"
    assert d["content"] == "Hello"


def test_chat_request_defaults():
    req = ChatRequest(model="deepseek-chat", messages=[])
    assert req.temperature == 0.7
    assert req.max_tokens == 4096
    assert req.stream is False


def test_chat_response_defaults():
    resp = ChatResponse(content="Hello world")
    assert resp.content == "Hello world"
    assert resp.finish_reason == "stop"


def test_delta_creation():
    delta = Delta(content="chunk")
    assert delta.content == "chunk"
    assert delta.tool_call_delta is None


def test_model_info_creation():
    info = ModelInfo(id="gpt-4o", name="gpt-4o", provider="openai")
    assert info.id == "gpt-4o"
    assert info.provider == "openai"


# --- YAML Config Edge Cases ---

def test_yaml_config_nonexistent_path():
    from pathlib import Path
    config = load_yaml_config(Path("/nonexistent/path/config.yaml"))
    assert "models" in config  # Falls back to defaults


def test_yaml_config_sandbox_settings():
    config = load_yaml_config()
    sandbox = config["sandbox"]
    assert sandbox["memory_limit"] == "512m"
    assert sandbox["cpu_limit"] == 1.0
    assert sandbox["timeout"] == 60


def test_yaml_config_orchestration():
    config = load_yaml_config()
    orch = config["orchestration"]
    assert orch["default_parallel_count"] == 3
    assert orch["agent_timeout"] == 300


def test_yaml_config_embedding():
    config = load_yaml_config()
    embed = config["embedding"]
    assert embed["model"] == "deepseek-embedding"
    assert embed["dimensions"] == 1536

