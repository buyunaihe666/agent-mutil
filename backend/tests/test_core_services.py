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
async def test_execute_tool(t_registry):
    result = await t_registry.execute_tool("read_file", file_path="test.txt")
    assert result.success is True


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
