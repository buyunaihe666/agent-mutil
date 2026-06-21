"""Tests for core service modules: conversation, agent, asset, tool registry,
sandbox, RAG, orchestration, and monitoring."""

import pytest
import asyncio

# --- Conversation Service Tests (M4) ---

from app.core.conversation_service import (
    ConversationStore,
    ConversationCreate,
    ConversationUpdate,
    ConversationStatus,
    ExportFormat,
    MessageCreate,
    conversation_store,
)


@pytest.fixture
def conv_store():
    store = ConversationStore()
    return store


@pytest.mark.asyncio
async def test_create_conversation(conv_store):
    conv = await conv_store.create_conversation("Hello world")
    assert conv["id"] is not None
    assert conv["status"] == "active"
    assert conv["message_count"] == 0


@pytest.mark.asyncio
async def test_list_conversations(conv_store):
    await conv_store.create_conversation("Test 1")
    await conv_store.create_conversation("Test 2")
    results, total = await conv_store.list_conversations()
    assert total == 2
    assert len(results) == 2


@pytest.mark.asyncio
async def test_conversation_update(conv_store):
    conv = await conv_store.create_conversation("Test")
    updated = await conv_store.update_conversation(
        conv["id"],
        ConversationUpdate(title="New Title", status=ConversationStatus.ARCHIVED),
    )
    assert updated["title"] == "New Title"
    assert updated["status"] == "archived"


@pytest.mark.asyncio
async def test_delete_conversation(conv_store):
    conv = await conv_store.create_conversation("Test")
    deleted = await conv_store.delete_conversation(conv["id"])
    assert deleted is True
    result = await conv_store.get_conversation(conv["id"])
    assert result is None


@pytest.mark.asyncio
async def test_add_message(conv_store):
    conv = await conv_store.create_conversation("Test")
    msg = await conv_store.add_message(
        conv["id"],
        MessageCreate(role="user", content="Hello"),
    )
    assert msg["id"] is not None
    assert msg["role"] == "user"
    assert msg["content"] == "Hello"


@pytest.mark.asyncio
async def test_get_messages_cursor(conv_store):
    conv = await conv_store.create_conversation("Test")
    for i in range(5):
        await conv_store.add_message(conv["id"], MessageCreate(role="user", content=f"Msg {i}"))
    page = await conv_store.get_messages(conv["id"], limit=3)
    assert len(page.messages) == 3
    assert page.has_more is True
    assert page.next_cursor is not None


@pytest.mark.asyncio
async def test_edit_message(conv_store):
    conv = await conv_store.create_conversation("Test")
    msg = await conv_store.add_message(conv["id"], MessageCreate(role="user", content="Original"))
    edited = await conv_store.edit_message(conv["id"], msg["id"], "Updated")
    assert edited["content"] == "Updated"
    assert edited["is_edited"] is True


@pytest.mark.asyncio
async def test_build_context(conv_store):
    conv = await conv_store.create_conversation("Test")
    for i in range(5):
        await conv_store.add_message(conv["id"], MessageCreate(role="user", content=f"Msg {i}"))
    ctx = await conv_store.build_context(conv["id"])
    assert len(ctx) == 5


@pytest.mark.asyncio
async def test_export_markdown(conv_store):
    conv = await conv_store.create_conversation("Test")
    await conv_store.add_message(conv["id"], MessageCreate(role="user", content="Hello"))
    exported = await conv_store.export_conversation(conv["id"], ExportFormat.MARKDOWN)
    assert "Hello" in exported
    assert "# " in exported


@pytest.mark.asyncio
async def test_export_json(conv_store):
    conv = await conv_store.create_conversation("Test")
    await conv_store.add_message(conv["id"], MessageCreate(role="user", content="Hello"))
    exported = await conv_store.export_conversation(conv["id"], ExportFormat.JSON)
    assert "Hello" in exported
    assert '"messages"' in exported


@pytest.mark.asyncio
async def test_regenerate_response(conv_store):
    conv = await conv_store.create_conversation("Test")
    msg = await conv_store.add_message(conv["id"], MessageCreate(role="user", content="Original"))
    regenerated = await conv_store.regenerate_response(conv["id"], msg["id"])
    assert regenerated is not None
    assert regenerated["role"] == "assistant"


# --- Agent Service Tests (M2) ---

from app.core.agent_service import (
    AgentStore,
    AgentCreate,
    AgentUpdate,
    AgentStatus,
    PermissionLevel,
    agent_store,
    PRESET_AGENTS,
    PRESET_TEMPLATES,
)


@pytest.fixture
def ag_store():
    store = AgentStore()
    return store


@pytest.mark.asyncio
async def test_preset_agents_initialized(ag_store):
    results, total = await ag_store.list_agents()
    assert total >= 3  # Three presets
    preset_names = [a["name"] for a in results]
    assert "数字主管" in preset_names


@pytest.mark.asyncio
async def test_preset_agents_not_deletable(ag_store):
    results, _ = await ag_store.list_agents()
    preset = next(a for a in results if a["name"] == "数字主管")
    with pytest.raises(ValueError, match="Preset agents cannot be deleted"):
        await ag_store.delete_agent(preset["id"])


@pytest.mark.asyncio
async def test_create_custom_agent(ag_store):
    agent = await ag_store.create_agent(AgentCreate(
        name="Test Agent",
        description="A test",
        tools=["file_read"],
    ))
    assert agent["id"] is not None
    assert agent["is_preset"] is False
    assert agent["is_active"] is True


@pytest.mark.asyncio
async def test_update_agent(ag_store):
    agent = await ag_store.create_agent(AgentCreate(
        name="Test Agent",
        system_prompt="Original prompt",
    ))
    updated = await ag_store.update_agent(
        agent["id"],
        AgentUpdate(name="Updated Agent", system_prompt="New prompt"),
    )
    assert updated["name"] == "Updated Agent"
    assert updated["system_prompt"] == "New prompt"


@pytest.mark.asyncio
async def test_delete_custom_agent(ag_store):
    agent = await ag_store.create_agent(AgentCreate(name="Test"))
    deleted = await ag_store.delete_agent(agent["id"])
    assert deleted is True
    result = await ag_store.get_agent(agent["id"])
    assert result is None


@pytest.mark.asyncio
async def test_agent_versions(ag_store):
    agent = await ag_store.create_agent(AgentCreate(
        name="Test Agent",
        system_prompt="v1",
    ))
    await ag_store.update_agent(agent["id"], AgentUpdate(system_prompt="v2"))
    versions = await ag_store.get_versions(agent["id"])
    assert len(versions) >= 2


@pytest.mark.asyncio
async def test_rollback_version(ag_store):
    agent = await ag_store.create_agent(AgentCreate(
        name="Test Agent",
        system_prompt="Original",
    ))
    await ag_store.update_agent(agent["id"], AgentUpdate(system_prompt="Modified"))
    rolled = await ag_store.rollback_version(agent["id"], 1)
    assert rolled["system_prompt"] == "Original"


def test_agent_templates_exist(ag_store):
    templates = ag_store.get_templates()
    assert len(templates) >= 5
    categories = set(t.category for t in templates)
    assert "分析" in categories


def test_get_template(ag_store):
    tpl = ag_store.get_template("template-code-review")
    assert tpl is not None
    assert tpl.name == "代码审查"


# --- Asset Service Tests (M5) ---

from app.core.asset_service import (
    AssetStore,
    AssetCreate,
    AssetUpdate,
    AssetType,
    StorageBackend,
    asset_store as global_asset_store,
    _get_preview_type,
    _human_size,
)


@pytest.fixture
def a_store():
    return AssetStore(storage_backend=StorageBackend.LOCAL)


def test_get_preview_type_image():
    assert _get_preview_type("image/png") == "image"
    assert _get_preview_type("image/jpeg") == "image"


def test_get_preview_type_pdf():
    assert _get_preview_type("application/pdf") == "pdf"


def test_get_preview_type_table():
    assert _get_preview_type("text/csv") == "table"


def test_get_preview_type_text():
    assert _get_preview_type("text/plain") == "text"


def test_get_preview_type_unknown():
    assert _get_preview_type("application/octet-stream") == "none"
    assert _get_preview_type(None) == "none"


def test_human_size():
    assert "B" in _human_size(500)
    assert "KB" in _human_size(2048)
    assert "MB" in _human_size(5 * 1024 * 1024)


@pytest.mark.asyncio
async def test_create_asset(a_store):
    asset = await a_store.create_asset(AssetCreate(
        filename="test.csv",
        original_filename="data.csv",
        file_path="assets/data.csv",
        file_size=1024,
        mime_type="text/csv",
        asset_type=AssetType.FILE,
    ))
    assert asset["id"] is not None
    assert asset["preview_type"] == "table"


@pytest.mark.asyncio
async def test_list_assets(a_store):
    await a_store.create_asset(AssetCreate(
        filename="file1.txt", original_filename="file1.txt", file_path="/tmp/f1.txt",
    ))
    await a_store.create_asset(AssetCreate(
        filename="file2.png", original_filename="file2.png", file_path="/tmp/f2.png",
        mime_type="image/png",
    ))
    results, total = await a_store.list_assets()
    assert total == 2


@pytest.mark.asyncio
async def test_search_assets(a_store):
    await a_store.create_asset(AssetCreate(
        filename="report.pdf", original_filename="report.pdf", file_path="/tmp/report.pdf",
    ))
    await a_store.create_asset(AssetCreate(
        filename="image.png", original_filename="image.png", file_path="/tmp/image.png",
    ))
    results, total = await a_store.list_assets(search="report")
    assert total == 1
    assert results[0]["filename"] == "report.pdf"


@pytest.mark.asyncio
async def test_delete_asset(a_store):
    asset = await a_store.create_asset(AssetCreate(
        filename="temp.txt", original_filename="temp.txt", file_path="/tmp/temp.txt",
    ))
    deleted = await a_store.delete_asset(asset["id"])
    assert deleted is True


@pytest.mark.asyncio
async def test_get_preview(a_store):
    asset = await a_store.create_asset(AssetCreate(
        filename="image.png", original_filename="image.png", file_path="/tmp/image.png",
        mime_type="image/png",
    ))
    preview = await a_store.get_preview(asset["id"])
    assert preview["preview_type"] == "image"
    assert "thumbnail_url" in preview


def test_storage_info(a_store):
    info = a_store.get_storage_info()
    assert info["backend"] == "local"
    assert info["total_files"] >= 0


# --- Tool Registry Tests (M8) ---

from app.core.tool_registry import (
    ToolRegistry,
    ToolCategory,
    ToolPermission,
    ToolResult,
    tool_registry,
)


@pytest.fixture
def t_registry():
    registry = ToolRegistry()
    return registry


def test_default_tools_registered(t_registry):
    assert t_registry.tool_count >= 7


def test_list_tools(t_registry):
    tools = t_registry.list_tools()
    assert len(tools) >= 7


def test_list_tools_by_category(t_registry):
    tools = t_registry.list_tools(category=ToolCategory.CODE_EXECUTION)
    assert len(tools) == 1
    assert tools[0].icon == "▶️"


def test_get_tool(t_registry):
    tool = t_registry.get("execute_code")
    assert tool is not None
    assert tool.definition.name == "code_execution"


def test_get_nonexistent_tool(t_registry):
    assert t_registry.get("nonexistent") is None


def test_get_function_definitions(t_registry):
    defs = t_registry.get_function_definitions(["execute_code", "read_file"])
    assert len(defs) == 2
    for d in defs:
        assert "function" in d
        assert "name" in d["function"]


def test_get_all_function_definitions(t_registry):
    defs = t_registry.get_all_function_definitions()
    assert len(defs) >= 5


def test_unregister_tool(t_registry):
    count_before = t_registry.tool_count
    t_registry.unregister("execute_code")
    assert t_registry.tool_count == count_before - 1
    assert t_registry.get("execute_code") is None


@pytest.mark.asyncio
async def test_execute_tool(t_registry, tmp_path):
    # Create a real file in a temp dir and patch the config
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello", encoding="utf-8")
    with patch(
        "app.core.yaml_config.get_yaml_config",
        return_value={"storage": {"local_path": str(tmp_path)}},
    ):
        result = await t_registry.execute_tool("read_file", file_path="test.txt")
        assert result.success is True
        assert result.data["content"] == "hello"


@pytest.mark.asyncio
async def test_execute_nonexistent_tool(t_registry):
    result = await t_registry.execute_tool("nonexistent")
    assert result.success is False
    assert "not found" in result.error


@pytest.mark.asyncio
async def test_code_execution_audit_tool(t_registry):
    result = await t_registry.execute_tool("audit_code", code="eval('malicious')")
    assert result.success is True
    assert result.data is not None
    assert "audit_summary" in result.data


def test_audit_tool_category(t_registry):
    tools = t_registry.list_tools(category=ToolCategory.CODE_EXECUTION_AUDIT)
    assert len(tools) == 1
    assert tools[0].name == "code_execution_audit"


# --- DatabaseQueryTool Tests ---

from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_query_tool_empty_query(t_registry):
    """Empty query should be rejected."""
    result = await t_registry.execute_tool("query_database", query="")
    assert result.success is False
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_query_tool_reject_insert(t_registry):
    """INSERT statement should be rejected."""
    result = await t_registry.execute_tool("query_database",
        query="INSERT INTO users (name) VALUES ('test')")
    assert result.success is False
    assert "INSERT" in result.error


@pytest.mark.asyncio
async def test_query_tool_reject_update(t_registry):
    """UPDATE statement should be rejected."""
    result = await t_registry.execute_tool("query_database",
        query="UPDATE users SET name = 'hacked' WHERE id = 1")
    assert result.success is False
    assert "UPDATE" in result.error


@pytest.mark.asyncio
async def test_query_tool_reject_delete(t_registry):
    """DELETE statement should be rejected."""
    result = await t_registry.execute_tool("query_database",
        query="DELETE FROM users WHERE id = 1")
    assert result.success is False
    assert "DELETE" in result.error


@pytest.mark.asyncio
async def test_query_tool_reject_drop(t_registry):
    """DROP statement should be rejected."""
    result = await t_registry.execute_tool("query_database",
        query="DROP TABLE users")
    assert result.success is False
    assert "DROP" in result.error


@pytest.mark.asyncio
async def test_query_tool_reject_comment_injection(t_registry):
    """Comment-based SQL injection should be rejected."""
    result = await t_registry.execute_tool("query_database",
        query="SELECT * FROM users WHERE name = 'admin' --'")
    assert result.success is False
    assert "injection" in result.error.lower()


@pytest.mark.asyncio
async def test_query_tool_reject_or_injection(t_registry):
    """OR-based SQL injection should be rejected."""
    result = await t_registry.execute_tool("query_database",
        query="SELECT * FROM users WHERE name = 'x' OR '1'='1'")
    assert result.success is False
    assert "injection" in result.error.lower()


@pytest.mark.asyncio
async def test_query_tool_reject_stacked_query(t_registry):
    """Stacked query injection should be rejected."""
    result = await t_registry.execute_tool("query_database",
        query="SELECT * FROM users; DROP TABLE users")
    assert result.success is False
    # Caught by either injection patterns or write keyword check (DROP)
    err = result.error.lower()
    assert "injection" in err or "drop" in err or "select and with" in err.lower()


@pytest.mark.asyncio
async def test_query_tool_accept_valid_select(t_registry):
    """Valid SELECT query should be accepted and executed."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.keys.return_value = ["id", "name"]
    # Use a tuple so zip(columns, row) works naturally
    mock_result.fetchall.return_value = [(1, "test")]
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    async def mock_get_db():
        yield mock_session

    with patch("app.core.tool_registry.get_db", side_effect=mock_get_db):
        result = await t_registry.execute_tool("query_database",
            query="SELECT id, name FROM users LIMIT 10")
        assert result.success is True
        assert result.data is not None
        assert "columns" in result.data
        assert result.data["columns"] == ["id", "name"]
        assert len(result.data["rows"]) == 1
        assert result.data["rows"][0] == {"id": 1, "name": "test"}


@pytest.mark.asyncio
async def test_query_tool_accept_cte(t_registry):
    """WITH (CTE) query should be accepted."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.keys.return_value = ["count"]
    mock_result.fetchall.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    async def mock_get_db():
        yield mock_session

    with patch("app.core.tool_registry.get_db", side_effect=mock_get_db):
        result = await t_registry.execute_tool("query_database",
            query="WITH active_users AS (SELECT * FROM users WHERE active = true) SELECT count(*) FROM active_users")
        assert result.success is True


@pytest.mark.asyncio
async def test_query_tool_db_error_handling(t_registry):
    """Database errors should be caught and returned gracefully."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(side_effect=Exception("Connection refused"))
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    async def mock_get_db():
        yield mock_session

    with patch("app.core.tool_registry.get_db", side_effect=mock_get_db):
        result = await t_registry.execute_tool("query_database",
            query="SELECT * FROM users")
        assert result.success is False
        assert "Connection refused" in result.error


# --- FileReadTool Tests ---

import os
import tempfile
from pathlib import Path
from unittest.mock import patch


class TestFileReadTool:
    """Tests for FileReadTool with real file I/O."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create a temporary storage root for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_root = Path(self.temp_dir.name).resolve()
        # Patch storage.local_path to point to our temp dir
        self._patch = patch(
            "app.core.yaml_config.get_yaml_config",
            return_value={"storage": {"local_path": str(self.storage_root)}},
        )
        self._patch.start()
        yield
        self._patch.stop()
        self.temp_dir.cleanup()

    def _create_file(self, rel_path: str, content: str = "hello world") -> Path:
        """Helper: create a file under the temp storage root."""
        full_path = self.storage_root / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return full_path

    @pytest.mark.asyncio
    async def test_file_read_empty_path(self, t_registry):
        """Empty path should return error."""
        result = await t_registry.execute_tool("read_file", file_path="")
        assert result.success is False
        assert "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_file_read_path_traversal_attack(self, t_registry):
        """Path traversal attack (e.g. ../../../etc/passwd) should be rejected."""
        result = await t_registry.execute_tool(
            "read_file", file_path="../../../etc/passwd"
        )
        assert result.success is False
        assert "outside" in result.error.lower()

    @pytest.mark.asyncio
    async def test_file_read_not_found(self, t_registry):
        """Non-existent file should return error."""
        result = await t_registry.execute_tool(
            "read_file", file_path="nonexistent.txt"
        )
        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_file_read_directory_not_file(self, t_registry):
        """Directory path should return error."""
        subdir = self.storage_root / "subdir"
        subdir.mkdir(exist_ok=True)
        result = await t_registry.execute_tool("read_file", file_path="subdir")
        assert result.success is False
        assert "not a file" in result.error.lower()

    @pytest.mark.asyncio
    async def test_file_read_success(self, t_registry):
        """Reading a valid text file should return its content."""
        self._create_file("notes.txt", "Hello from NEXUS AI!")
        result = await t_registry.execute_tool("read_file", file_path="notes.txt")
        assert result.success is True
        assert result.data is not None
        assert result.data["content"] == "Hello from NEXUS AI!"
        assert result.data["size"] == 20
        assert result.data["path"] == "notes.txt"

    @pytest.mark.asyncio
    async def test_file_read_too_large(self, t_registry):
        """Files larger than 10MB should be rejected."""
        big_path = self._create_file("big_file.txt", "x")
        # Simulate a file larger than 10MB by patching stat
        mock_stat = os.stat(str(big_path))
        mock_stat_result = list(mock_stat)
        # Set file size to 11MB
        mock_stat_result[6] = 11 * 1024 * 1024
        import stat as stat_module

        class MockStatResult:
            def __init__(self, values):
                self._values = values

            def __getattr__(self, name):
                # map stat result tuple indices
                mapping = {
                    "st_mode": 0, "st_ino": 1, "st_dev": 2, "st_nlink": 3,
                    "st_uid": 4, "st_gid": 5, "st_size": 6,
                    "st_atime": 7, "st_mtime": 8, "st_ctime": 9,
                }
                if name in mapping:
                    return self._values[mapping[name]]
                raise AttributeError(name)

        with patch.object(Path, "stat", return_value=MockStatResult(mock_stat_result)):
            result = await t_registry.execute_tool("read_file", file_path="big_file.txt")
            assert result.success is False
            assert "too large" in result.error.lower()

    @pytest.mark.asyncio
    async def test_file_read_binary_file_metadata(self, t_registry):
        """Binary files should return metadata only, not content."""
        bin_path = self.storage_root / "image.bin"
        bin_path.write_bytes(b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d")
        result = await t_registry.execute_tool("read_file", file_path="image.bin")
        assert result.success is True
        assert result.data is not None
        assert result.data["content"] == "[binary file]"
        assert result.data["size"] == 12
        assert result.data["path"] == "image.bin"

    @pytest.mark.asyncio
    async def test_file_read_nested_subdirectory(self, t_registry):
        """Files in nested subdirectories should be readable."""
        self._create_file("a/b/c/deep.txt", "deep content")
        result = await t_registry.execute_tool(
            "read_file", file_path="a/b/c/deep.txt"
        )
        assert result.success is True
        assert result.data["content"] == "deep content"


# --- WebSearchTool Tests ---

from unittest.mock import AsyncMock, patch
import httpx


@pytest.mark.asyncio
async def test_web_search_empty_query(t_registry):
    """Empty query should return error."""
    result = await t_registry.execute_tool("search_web", query="")
    assert result.success is False
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_web_search_success(t_registry):
    """Successful search should return results with title/url/snippet."""
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "AbstractText": "Python is a programming language.",
        "AbstractURL": "https://en.wikipedia.org/wiki/Python",
        "Heading": "Python (programming language)",
        "RelatedTopics": [
            {
                "Text": "Python is widely used in data science.",
                "FirstURL": "https://en.wikipedia.org/wiki/Python_(data_science)",
            },
            {
                "Text": "Python supports multiple paradigms.",
                "FirstURL": "https://en.wikipedia.org/wiki/Python_(programming_paradigm)",
            },
        ],
    })

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await t_registry.execute_tool("search_web", query="Python")

    assert result.success is True
    assert "Found" in result.output
    assert "results" in result.data
    assert len(result.data["results"]) >= 1
    # First result should have all three fields
    first = result.data["results"][0]
    assert "title" in first
    assert "url" in first
    assert "snippet" in first


@pytest.mark.asyncio
async def test_web_search_no_results(t_registry):
    """Empty results should still return success with empty list."""
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "AbstractText": "",
        "RelatedTopics": [],
    })

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await t_registry.execute_tool("search_web", query="xyznonexistent12345")

    assert result.success is True
    assert result.data["results"] == []


@pytest.mark.asyncio
async def test_web_search_http_error(t_registry):
    """HTTP errors should be handled gracefully."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    error_response = AsyncMock()
    error_response.status_code = 500
    mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
        "Server error", request=AsyncMock(), response=error_response,
    ))

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await t_registry.execute_tool("search_web", query="test")

    assert result.success is False
    assert "HTTP 500" in result.error


@pytest.mark.asyncio
async def test_web_search_timeout(t_registry):
    """Timeout errors should be handled gracefully."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await t_registry.execute_tool("search_web", query="test")

    assert result.success is False
    assert "timed out" in result.error.lower()


@pytest.mark.asyncio
async def test_web_search_network_error(t_registry):
    """General network errors should be handled gracefully."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(side_effect=Exception("Network unreachable"))

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await t_registry.execute_tool("search_web", query="test")

    assert result.success is False
    assert "Network unreachable" in result.error


# --- Sandbox Manager Tests (M7) ---

from app.core.sandbox_manager import (
    SandboxManager,
    ASTAnalyzer,
    ExecutionRisk,
    SandboxStatus,
    sandbox_manager,
)


@pytest.fixture
def sb_manager():
    return SandboxManager()


def test_ast_analyze_safe_code():
    risk, findings = ASTAnalyzer.analyze("print('hello world')\nx = 1 + 2")
    assert risk == ExecutionRisk.SAFE


def test_ast_analyze_detect_eval():
    risk, findings = ASTAnalyzer.analyze("eval('2 + 2')")
    assert risk == ExecutionRisk.DANGEROUS


def test_ast_analyze_block_import_pty():
    risk, findings = ASTAnalyzer.analyze("import pty\npty.spawn('/bin/bash')")
    assert risk == ExecutionRisk.BLOCKED


def test_ast_analyze_block_os_system():
    risk, findings = ASTAnalyzer.analyze("import os\nos.system('rm -rf /')")
    assert risk == ExecutionRisk.BLOCKED


def test_ast_analyze_warn_import_os():
    risk, findings = ASTAnalyzer.analyze("import os\nprint(os.getcwd())")
    assert risk in (ExecutionRisk.SAFE, ExecutionRisk.WARNING)


def test_ast_analyze_syntax_error():
    risk, findings = ASTAnalyzer.analyze("def broken(:\n    pass")
    assert risk == ExecutionRisk.BLOCKED


@pytest.mark.asyncio
async def test_sandbox_execute_safe_code(sb_manager):
    result = await sb_manager.execute("print('hello')", language="python")
    assert result.status == SandboxStatus.COMPLETED


@pytest.mark.asyncio
async def test_sandbox_execute_blocked_code(sb_manager):
    result = await sb_manager.execute("import pty\npty.spawn('/bin/bash')")
    assert result.status == SandboxStatus.ERROR
    assert "blocked" in result.error.lower()


@pytest.mark.asyncio
async def test_sandbox_cancel_execution(sb_manager):
    result = await sb_manager.execute("print('test')")
    cancelled = await sb_manager.cancel_execution(result.execution_id)
    assert cancelled is True


def test_get_sandbox_info(sb_manager):
    info = sb_manager.get_sandbox_info()
    assert "memory_limit" in info
    assert "cpu_limit" in info
    assert "timeout" in info


# --- RAG Engine Tests (M6) ---

from app.core.rag_engine import (
    DocumentChunker,
    EmbeddingService,
    KnowledgeBaseEngine,
    DocumentChunk,
    Citation,
    knowledge_base_engine as global_rag_engine,
)


@pytest.fixture
def chunker():
    return DocumentChunker(max_chunk_tokens=512)


@pytest.fixture
def kb_engine():
    engine = KnowledgeBaseEngine()
    engine.clear()
    return engine


def test_chunker_small_text(chunker):
    chunks = chunker.chunk("Hello world, this is a test.", "test.txt")
    assert len(chunks) >= 1
    assert chunks[0].source_document == "test.txt"


def test_chunker_chinese_text(chunker):
    text = "你好世界。这是一个中文文档的测试。它包含多个句子。每个句子都会被分块处理。"
    chunks = chunker.chunk(text, "cn.txt")
    assert len(chunks) >= 1


def test_chunker_long_text(chunker):
    text = "Paragraph one. " * 100 + "\n\n" + "Paragraph two. " * 100
    chunks = chunker.chunk(text, "long.txt")
    assert len(chunks) >= 2


def test_chunker_creates_unique_ids(chunker):
    chunks = chunker.chunk("Some text for testing.", "test.txt")
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))  # All unique


@pytest.mark.asyncio
async def test_embedding_service(kb_engine):
    texts = ["Hello world", "Another text"]
    embeddings = await kb_engine.embedding_service.embed(texts)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == kb_engine.embedding_service.dimensions


@pytest.mark.asyncio
async def test_ingest_document(kb_engine):
    text = "This is a document about machine learning. " * 10
    chunks = await kb_engine.ingest_document(text, "ml_doc.txt")
    assert len(chunks) >= 1
    assert kb_engine.get_document_count() == 1


@pytest.mark.asyncio
async def test_vector_search(kb_engine):
    await kb_engine.ingest_document("Python is a programming language.", "doc1.txt")
    await kb_engine.ingest_document("Machine learning is fascinating.", "doc2.txt")
    results = await kb_engine.search("Python programming", top_k=3, search_type="vector")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_keyword_search(kb_engine):
    await kb_engine.ingest_document("Python programming guide.", "doc1.txt")
    results = await kb_engine.search("Python", top_k=5, search_type="keyword")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_hybrid_search(kb_engine):
    await kb_engine.ingest_document("Python programming language guide.", "doc1.txt")
    await kb_engine.ingest_document("Cooking recipes for beginners.", "doc2.txt")
    results = await kb_engine.search("programming", top_k=5, search_type="hybrid")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_search_with_citations(kb_engine):
    await kb_engine.ingest_document("Python is a popular programming language.", "python.txt")
    results, citations = await kb_engine.search_with_citations("Python", top_k=3)
    assert len(citations) >= 1
    assert all(isinstance(c, Citation) for c in citations)


def test_clear_engine(kb_engine):
    kb_engine.clear()
    assert kb_engine.get_chunk_count() == 0
    assert kb_engine.get_document_count() == 0


# --- Orchestration Engine Tests (M3) ---

from app.core.orchestration_engine import (
    OrchestrationEngine,
    OrchestrationPlan,
    SubTask,
    StepResult,
    TaskStatus,
    StepStatus,
    VariableEntry,
    orchestration_engine as global_orch_engine,
)


@pytest.fixture
def orch_engine():
    return OrchestrationEngine()


@pytest.mark.asyncio
async def test_create_plan(orch_engine):
    available_agents = [{"id": "agent-1", "name": "Test Agent"}]
    plan = await orch_engine.create_plan(
        title="Test Task",
        subtask_descriptions=["Step one", "Step two", "Step three"],
        available_agents=available_agents,
    )
    assert len(plan.subtasks) == 3
    assert plan.total_estimated_steps == 3
    assert plan.plan_id is not None


@pytest.mark.asyncio
async def test_plan_subtasks_have_agents(orch_engine):
    plan = await orch_engine.create_plan(
        title="Test",
        subtask_descriptions=["Task A", "Task B"],
        available_agents=[{"id": "a1", "name": "Agent 1"}, {"id": "a2", "name": "Agent 2"}],
    )
    assert plan.subtasks[0].assigned_agent_id is not None


@pytest.mark.asyncio
async def test_execute_plan(orch_engine):
    plan = await orch_engine.create_plan(
        title="Simple Task",
        subtask_descriptions=["Step 1", "Step 2"],
        available_agents=[],
    )
    results = await orch_engine.execute_plan(plan.plan_id)
    assert len(results) == 2
    assert all(r.status == StepStatus.COMPLETED for r in results)


@pytest.mark.asyncio
async def test_pause_resume_plan(orch_engine):
    plan = await orch_engine.create_plan(
        title="Pausable Task",
        subtask_descriptions=["Step"],
        available_agents=[],
    )
    assert orch_engine.get_status(plan.plan_id) == TaskStatus.PENDING
    await orch_engine.execute_plan(plan.plan_id)
    assert orch_engine.get_status(plan.plan_id) == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_cancel_plan(orch_engine):
    plan = await orch_engine.create_plan(
        title="Cancel Test",
        subtask_descriptions=["Step"],
        available_agents=[],
    )
    cancelled = await orch_engine.cancel(plan.plan_id)
    assert cancelled is True
    assert orch_engine.get_status(plan.plan_id) == TaskStatus.CANCELLED


@pytest.mark.asyncio
async def test_variable_table(orch_engine):
    plan = await orch_engine.create_plan(
        title="Var Test",
        subtask_descriptions=["Step"],
        available_agents=[],
    )
    await orch_engine.set_variable(plan.plan_id, "mykey", {"result": 42})
    entry = await orch_engine.get_variable(plan.plan_id, "mykey")
    assert entry is not None
    assert entry.value == {"result": 42}


@pytest.mark.asyncio
async def test_parallel_groups(orch_engine):
    plan = await orch_engine.create_plan(
        title="Parallel Test",
        subtask_descriptions=["Independent A", "Independent B", "After using the result C"],
        available_agents=[],
    )
    assert len(plan.parallel_groups) >= 1


@pytest.mark.asyncio
async def test_execute_step_retry(orch_engine):
    """Step should retry on transient failure up to step_retry_count times."""
    from unittest.mock import AsyncMock, patch

    plan = await orch_engine.create_plan(
        title="Retry Test",
        subtask_descriptions=["Step that fails transiently"],
        available_agents=[{"id": "agent-1", "name": "Test Agent"}],
    )
    call_count = 0

    async def mock_chat_completion(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Transient connection error")
        from types import SimpleNamespace
        return SimpleNamespace(content="Success after retry")

    mock_agent_store = AsyncMock()
    mock_agent_store.get_agent = AsyncMock(return_value={
        "id": "agent-1", "name": "Test Agent", "system_prompt": "You are a test agent.",
        "default_model": "test", "temperature": 0.5, "max_tokens": 1024,
    })

    with patch("app.core.agent_service.agent_store", mock_agent_store), \
         patch("app.core.llm_gateway.chat_completion", side_effect=mock_chat_completion):
        result = await orch_engine._execute_step(plan.plan_id, plan.subtasks[0].step_id)

    assert result.status == StepStatus.COMPLETED
    assert result.retry_count == 2  # Failed twice, succeeded on 3rd attempt
    assert "Success after retry" in result.output


@pytest.mark.asyncio
async def test_execute_step_non_retryable(orch_engine):
    """Step should NOT retry on non-retryable errors like ValueError."""
    from unittest.mock import AsyncMock, patch

    plan = await orch_engine.create_plan(
        title="Non-Retryable Test",
        subtask_descriptions=["Step with validation error"],
        available_agents=[{"id": "agent-1", "name": "Test Agent"}],
    )

    async def mock_chat_completion(*args, **kwargs):
        raise ValueError("Invalid input data")

    mock_agent_store = AsyncMock()
    mock_agent_store.get_agent = AsyncMock(return_value={
        "id": "agent-1", "name": "Test Agent", "system_prompt": "You are a test agent.",
        "default_model": "test", "temperature": 0.5, "max_tokens": 1024,
    })

    with patch("app.core.agent_service.agent_store", mock_agent_store), \
         patch("app.core.llm_gateway.chat_completion", side_effect=mock_chat_completion):
        result = await orch_engine._execute_step(plan.plan_id, plan.subtasks[0].step_id)

    assert result.status == StepStatus.FAILED
    assert result.retry_count == 0  # No retries for non-retryable error
    assert "Invalid input data" in result.error


@pytest.mark.asyncio
async def test_pause_resume_during_execution(orch_engine):
    """Plan should pause when requested and resume correctly.

    Uses an agent with a mock slow LLM so pause can be triggered
    between parallel groups.
    """
    from unittest.mock import AsyncMock, patch

    # Build subtasks explicitly with separate parallel groups
    from app.core.orchestration_engine import SubTask, DependencyType
    s1 = SubTask(description="Step A", assigned_agent_id="agent-delay", assigned_agent_name="Slow Agent")
    s2 = SubTask(description="Step B", assigned_agent_id="agent-delay", assigned_agent_name="Slow Agent",
                  dependencies=[s1.step_id], dependency_type=DependencyType.SEQUENTIAL)

    plan = await orch_engine.create_plan(
        title="Pause Test",
        subtask_descriptions=[],  # Not used when subtasks provided
        available_agents=[],
        subtasks=[s1, s2],
    )
    # Verify two separate parallel groups
    assert len(plan.parallel_groups) == 2, f"Expected 2 groups, got {len(plan.parallel_groups)}"

    async def slow_completion(*args, **kwargs):
        await asyncio.sleep(0.3)
        from types import SimpleNamespace
        return SimpleNamespace(content="Done")

    mock_agent_store = AsyncMock()
    mock_agent_store.get_agent = AsyncMock(return_value={
        "id": "agent-delay", "name": "Slow Agent", "system_prompt": "You are a test agent.",
        "default_model": "test", "temperature": 0.5, "max_tokens": 1024,
    })

    async def run_plan():
        return await orch_engine.execute_plan(plan.plan_id)

    with patch("app.core.agent_service.agent_store", mock_agent_store), \
         patch("app.core.llm_gateway.chat_completion", side_effect=slow_completion):
        bg_task = asyncio.create_task(run_plan())

        # Give it a moment to start executing the first group
        await asyncio.sleep(0.1)

        # Pause should succeed during RUNNING
        paused = await orch_engine.pause(plan.plan_id)
        assert paused is True, f"pause returned False, status={orch_engine.get_status(plan.plan_id)}"
        assert orch_engine.get_status(plan.plan_id) == TaskStatus.PAUSED

        # Resume
        resumed = await orch_engine.resume(plan.plan_id)
        assert resumed is True
        assert orch_engine.get_status(plan.plan_id) == TaskStatus.RUNNING

        # Wait for completion
        results = await bg_task

    assert len(results) == 2
    assert orch_engine.get_status(plan.plan_id) == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_cancel_during_execution(orch_engine):
    """Cancel should stop plan execution and skip remaining steps."""
    plan = await orch_engine.create_plan(
        title="Cancel Test",
        subtask_descriptions=["Step A", "Step B"],
        available_agents=[],
    )

    cancel_called = False

    async def run_plan():
        return await orch_engine.execute_plan(plan.plan_id)

    bg_task = asyncio.create_task(run_plan())
    await asyncio.sleep(0.05)

    cancelled = await orch_engine.cancel(plan.plan_id)
    assert cancelled is True
    assert orch_engine.get_status(plan.plan_id) == TaskStatus.CANCELLED

    results = await bg_task
    # All steps should be either completed or skipped
    assert orch_engine.get_status(plan.plan_id) == TaskStatus.CANCELLED


@pytest.mark.asyncio
async def test_step_event_callback(orch_engine):
    """Engine should emit correct events through callback during execution."""
    events = []

    async def track_events(event_type: str, plan_id: str, data: dict | None):
        events.append({"type": event_type, "plan_id": plan_id, "data": data})

    plan = await orch_engine.create_plan(
        title="Event Test",
        subtask_descriptions=["Step 1"],
        available_agents=[],
    )

    results = await orch_engine.execute_plan(plan.plan_id, on_event=track_events)

    assert len(results) == 1
    event_types = [e["type"] for e in events]
    assert "step_started" in event_types
    assert "step_completed" in event_types
    assert "plan_completed" in event_types


@pytest.mark.asyncio
async def test_compute_parallel_groups_topological(orch_engine):
    """Parallel groups should respect explicit dependency step_ids."""
    from app.core.orchestration_engine import SubTask, DependencyType

    s1 = SubTask(description="Independent A")
    s2 = SubTask(description="Depends on A", dependencies=[s1.step_id],
                  dependency_type=DependencyType.SEQUENTIAL)
    s3 = SubTask(description="Independent B")

    groups = orch_engine._compute_parallel_groups([s1, s2, s3])

    # s1 and s3 should be in first group (no deps), s2 in second group
    assert len(groups) == 2
    assert s1.step_id in groups[0]
    assert s3.step_id in groups[0]
    assert s2.step_id in groups[1]


# --- Monitor Service Tests (M10) ---

from app.core.monitor_service import (
    MonitorService,
    HardwareStats,
    ContainerStats,
    AgentActivity,
    AgentActivityStatus,
    SystemStats,
    monitor_service,
)


@pytest.fixture
def mon_service():
    return MonitorService()


@pytest.mark.asyncio
async def test_collect_hardware_stats(mon_service):
    stats = await mon_service.collect_hardware_stats()
    assert isinstance(stats, HardwareStats)
    assert stats.cpu_percent >= 0
    assert stats.memory_total_mb > 0


@pytest.mark.asyncio
async def test_collect_container_stats(mon_service):
    stats = await mon_service.collect_container_stats()
    assert len(stats) >= 1
    assert all(isinstance(s, ContainerStats) for s in stats)
    assert any(s.container_name == "nexus-postgres" for s in stats)


@pytest.mark.asyncio
async def test_update_agent_activity(mon_service):
    activity = AgentActivity(
        agent_id="agent-1",
        agent_name="Test Agent",
        agent_emoji="🤖",
        status=AgentActivityStatus.WORKING,
        message="Processing task",
    )
    await mon_service.update_agent_activity(activity)
    activities = await mon_service.get_agent_activities()
    assert len(activities) == 1
    assert activities[0].agent_name == "Test Agent"


@pytest.mark.asyncio
async def test_get_system_stats(mon_service):
    stats = await mon_service.get_system_stats()
    assert isinstance(stats, SystemStats)
    assert stats.hardware is not None
    assert len(stats.containers) >= 1


@pytest.mark.asyncio
async def test_monitoring_start_stop(mon_service):
    await mon_service.start_collection(interval=10)
    assert mon_service._is_collecting is True
    await mon_service.stop_collection()
    assert mon_service._is_collecting is False
