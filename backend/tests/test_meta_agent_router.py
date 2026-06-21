"""Tests for MetaAgentRouter — three-layer meta-agent orchestration."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.meta_agent_router import MetaAgentRouter


class MockAgentStore:
    """Mock agent store with preset meta and regular agents."""
    def __init__(self):
        self.agents = {
            "decision-1": {
                "id": "decision-1", "name": "智能决策", "is_meta": True,
                "tools": ["agent_communication"], "default_model": "deepseek-chat",
                "temperature": 0.3, "max_tokens": 4096,
                "system_prompt": "你是决策Agent...",
            },
            "strategy-1": {
                "id": "strategy-1", "name": "策略规划", "is_meta": True,
                "tools": ["agent_communication"], "default_model": "deepseek-chat",
                "temperature": 0.3, "max_tokens": 8192,
                "system_prompt": "你是策略Agent...",
            },
            "execution-1": {
                "id": "execution-1", "name": "执行调度", "is_meta": True,
                "tools": ["agent_communication", "web_search"], "default_model": "deepseek-chat",
                "temperature": 0.4, "max_tokens": 8192,
                "system_prompt": "你是执行Agent...",
            },
            "worker-1": {
                "id": "worker-1", "name": "数据专家", "is_meta": False,
                "tools": ["database_query", "code_execution", "file_read", "web_search"],
                "default_model": "deepseek-chat", "temperature": 0.4, "max_tokens": 8192,
                "system_prompt": "你是数据专家...",
            },
            "orchestrator-1": {
                "id": "orchestrator-1", "name": "数字主管", "is_meta": False,
                "tools": ["file_read", "agent_communication"], "default_model": "deepseek-chat",
                "temperature": 0.3, "max_tokens": 8192,
                "system_prompt": "你是数字主管...", "auto_execute": True,
            },
        }

    def get_agent(self, agent_id):
        return self.agents.get(agent_id)

    async def list_agents(self):
        agents = list(self.agents.values())
        return agents, len(agents)


@pytest.fixture
def agent_store():
    return MockAgentStore()


@pytest.fixture
def mock_engine():
    engine = MagicMock()
    engine.generate_plan = AsyncMock()
    engine.execute_plan = AsyncMock()
    return engine


@pytest.fixture
def router(agent_store, mock_engine):
    return MetaAgentRouter(
        agent_store=agent_store,
        orchestration_engine=mock_engine,
        llm_gateway=None,
    )


class TestMetaAgentRouterInit:
    def test_router_stores_dependencies(self, router, agent_store, mock_engine):
        assert router.agent_store is agent_store
        assert router.orchestration_engine is mock_engine
        assert router.llm_gateway is None


class TestGetMetaAgent:
    def test_finds_decision_agent(self, router):
        agent = router._get_meta_agent("decision")
        assert agent is not None
        assert agent["name"] == "智能决策"

    def test_finds_strategy_agent(self, router):
        agent = router._get_meta_agent("strategy")
        assert agent is not None
        assert agent["name"] == "策略规划"

    def test_finds_execution_agent(self, router):
        agent = router._get_meta_agent("execution")
        assert agent is not None
        assert agent["name"] == "执行调度"

    def test_returns_none_for_empty_type(self, router):
        agent = router._get_meta_agent("nonexistent")
        assert agent is None


class TestRoute:
    def make_callback(self):
        events = []
        async def cb(event_type, data):
            events.append((event_type, data))
        return events, cb

    @pytest.mark.asyncio
    async def test_routes_to_meta_pipeline_when_is_meta(self, router):
        events, cb = self.make_callback()
        router._run_meta_pipeline = AsyncMock(return_value="meta result")
        result = await router.route(
            message="帮我分析竞品数据",
            conversation_id="conv-1",
            orchestrator_agent_id="decision-1",
            orchestrator_model="deepseek-chat",
            ws_event_callback=cb,
        )
        assert result == "meta result"
        router._run_meta_pipeline.assert_called_once()

    @pytest.mark.asyncio
    async def test_routes_to_flat_when_not_is_meta(self, router):
        events, cb = self.make_callback()
        router._run_flat_orchestration = AsyncMock(return_value="flat result")
        result = await router.route(
            message="帮我分析竞品数据",
            conversation_id="conv-1",
            orchestrator_agent_id="orchestrator-1",
            orchestrator_model="deepseek-chat",
            ws_event_callback=cb,
        )
        assert result == "flat result"
        router._run_flat_orchestration.assert_called_once()


class TestRunDecisionLayer:
    @pytest.mark.asyncio
    async def test_returns_triage_simple(self, router):
        with patch("app.core.meta_agent_router.chat_completion") as mock_cc:
            mock_cc.return_value = _mock_chat_response(json.dumps({
                "complexity": "simple", "reasoning": "简单查询",
                "suggested_agent_name": "数据专家", "needs_plan": False,
            }))
            agent = router._get_meta_agent("decision")
            triage = await router._run_decision_layer("今天天气怎么样", agent, "deepseek-chat")
            assert triage["complexity"] == "simple"

    @pytest.mark.asyncio
    async def test_returns_triage_complex(self, router):
        with patch("app.core.meta_agent_router.chat_completion") as mock_cc:
            mock_cc.return_value = _mock_chat_response(json.dumps({
                "complexity": "complex", "reasoning": "需多Agent协作",
                "suggested_direction": "搜索+分析", "needs_plan": True,
            }))
            agent = router._get_meta_agent("decision")
            triage = await router._run_decision_layer("分析竞品并生成报告", agent, "deepseek-chat")
            assert triage["complexity"] == "complex"
            assert triage["needs_plan"] is True

    @pytest.mark.asyncio
    async def test_fallback_on_json_parse_error(self, router):
        with patch("app.core.meta_agent_router.chat_completion") as mock_cc:
            mock_cc.return_value = _mock_chat_response("not valid json ```")
            agent = router._get_meta_agent("decision")
            triage = await router._run_decision_layer("anything", agent, "deepseek-chat")
            assert triage["complexity"] == "simple"


class TestRunMetaPipeline:
    def make_callback(self):
        events = []
        async def cb(event_type, data):
            events.append(event_type)
        return events, cb

    @pytest.mark.asyncio
    async def test_simple_shortcut(self, router):
        with patch("app.core.meta_agent_router.chat_completion") as mock_cc:
            mock_cc.return_value = _mock_chat_response(json.dumps({
                "complexity": "simple", "reasoning": "简单查询",
                "suggested_agent_name": "数据专家", "needs_plan": False,
            }))
            events, cb = self.make_callback()
            router._delegate_simple = AsyncMock(return_value="直接回答")
            agent = router._get_meta_agent("decision")
            result = await router._run_meta_pipeline(
                "1+1等于几", "conv-1", agent, "deepseek-chat", cb,
            )
            assert result == "直接回答"
            assert "meta_agent_started" in events

    @pytest.mark.asyncio
    async def test_complex_triggers_full_pipeline(self, router, mock_engine):
        with (
            patch("app.core.meta_agent_router.chat_completion") as mock_cc,
            patch("app.core.meta_agent_router.chat_completion_stream") as mock_cs,
        ):
            mock_cc.return_value = _mock_chat_response(json.dumps({
                "complexity": "complex", "reasoning": "复杂任务",
                "suggested_direction": "...", "needs_plan": True,
            }))
            from app.core.orchestration_engine import OrchestrationPlan
            mock_plan = OrchestrationPlan(
                plan_id="plan-1", title="测试计划", subtasks=[], parallel_groups=[],
                total_estimated_steps=0, variable_table_keys=[],
            )
            mock_engine.generate_plan.return_value = mock_plan
            mock_engine.execute_plan.return_value = []
            # mock streaming review
            chunks = [_mock_stream_delta("总结"), _mock_stream_delta("完成")]
            mock_cs.return_value = _async_iter(chunks)

            events, cb = self.make_callback()
            router._wait_for_approval = AsyncMock(return_value=True)
            agent = router._get_meta_agent("decision")
            result = await router._run_meta_pipeline(
                "分析竞品数据", "conv-1", agent, "deepseek-chat", cb,
            )
            assert "总结完成" in result
            mock_engine.generate_plan.assert_called_once()
            mock_engine.execute_plan.assert_called_once()


# --- Helpers ---

def _mock_chat_response(content: str):
    """Build a mock ChatResponse matching llm_gateway.ChatResponse shape."""
    from app.core.llm_gateway import ChatResponse
    return ChatResponse(content=content, model="deepseek-chat", finish_reason="stop")


def _mock_stream_delta(content: str):
    """Build a mock Delta matching llm_gateway.Delta shape."""
    from app.core.llm_gateway import Delta
    return Delta(content=content)


async def _async_iter(items):
    for item in items:
        yield item
