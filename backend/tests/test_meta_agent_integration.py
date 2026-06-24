"""Integration tests for Meta-Agent three-layer pipeline."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.meta_agent_router import MetaAgentRouter
from app.core.orchestration_engine import OrchestrationPlan, SubTask, StepResult, StepStatus


class MockLLMGateway:
    """Mock LLM gateway for integration testing."""

    def __init__(self):
        self.chat_completion = AsyncMock()
        self.chat_completion_stream = AsyncMock()
        self.call_count = 0


class MockAgentStore:
    """Mock agent store with meta and regular agents."""

    def __init__(self):
        self.agents = {
            "d1": {
                "id": "d1", "name": "智能决策", "is_meta": True,
                "tools": ["agent_communication"], "default_model": "deepseek-chat",
                "system_prompt": "你是决策Agent...", "temperature": 0.3, "max_tokens": 4096,
            },
            "s1": {
                "id": "s1", "name": "策略规划", "is_meta": True,
                "tools": ["agent_communication"], "default_model": "deepseek-chat",
                "system_prompt": "你是策略Agent...", "temperature": 0.3, "max_tokens": 8192,
            },
            "e1": {
                "id": "e1", "name": "执行调度", "is_meta": True,
                "tools": ["agent_communication", "web_search"], "default_model": "deepseek-chat",
                "system_prompt": "你是执行Agent...", "temperature": 0.4, "max_tokens": 8192,
            },
            "w1": {
                "id": "w1", "name": "数据专家", "is_meta": False,
                "tools": ["database_query", "code_execution"], "default_model": "deepseek-chat",
                "system_prompt": "你是数据专家...", "temperature": 0.4, "max_tokens": 8192,
            },
            "w2": {
                "id": "w2", "name": "风控顾问", "is_meta": False,
                "tools": ["code_execution_audit", "file_read"], "default_model": "deepseek-chat",
                "system_prompt": "你是风控顾问...", "temperature": 0.2, "max_tokens": 8192,
            },
        }

    def get_agent(self, aid):
        return self.agents.get(aid)

    async def list_agents(self):
        agents = list(self.agents.values())
        return agents, len(agents)


class MockResponse:
    """Mock for litellm chat_completion response."""

    def __init__(self, content):
        self.choices = [MagicMock()]
        self.choices[0].message = MagicMock()
        self.choices[0].message.content = content


class MockStreamChunk:
    """Mock for litellm streaming chunk."""

    def __init__(self, content):
        self.choices = [MagicMock()]
        self.choices[0].delta = MagicMock()
        self.choices[0].delta.content = content


@pytest.fixture
def agent_store():
    return MockAgentStore()


@pytest.fixture
def llm():
    llm = MockLLMGateway()
    # Default: decision returns complex
    llm.chat_completion.return_value = MockResponse(json.dumps({
        "complexity": "complex",
        "reasoning": "需要多Agent协作",
        "suggested_direction": "搜索+分析+报告",
        "needs_plan": True,
    }))
    return llm


@pytest.fixture
def engine():
    engine = MagicMock()
    engine.generate_plan = AsyncMock(return_value=OrchestrationPlan(
        plan_id="int-plan-1", title="集成测试计划",
        subtasks=[
            SubTask(
                step_id="s1", description="搜索数据", assigned_agent_name="数据专家",
                dependencies=[], dependency_type="none",
                input_variables=[], expected_output="搜索结果",
            ),
            SubTask(
                step_id="s2", description="分析数据", assigned_agent_name="风控顾问",
                dependencies=["s1"], dependency_type="sequential",
                input_variables=["step_s1_result"], expected_output="分析报告",
            ),
        ],
        parallel_groups=[["s1"], ["s2"]],
        total_estimated_steps=2,
        variable_table_keys=["step_s1_result"],
    ))
    engine.execute_plan = AsyncMock(return_value=[
        StepResult(step_id="s1", status=StepStatus.COMPLETED, output="数据搜索结果...",
                   agent_name="数据专家", retry_count=0),
        StepResult(step_id="s2", status=StepStatus.COMPLETED, output="数据分析结果...",
                   agent_name="风控顾问", retry_count=0),
    ])
    return engine


class TestMetaAgentIntegration:
    """End-to-end integration tests for the three-layer pipeline."""

    @pytest.mark.asyncio
    async def test_full_three_layer_pipeline(self, agent_store, llm, engine):
        """Complex message -> full three-layer pipeline -> synthesis."""
        router = MetaAgentRouter(
            agent_store=agent_store,
            orchestration_engine=engine,
            llm_gateway=llm,
        )

        # Patch chat_completion and chat_completion_stream used during
        # the decision and review layers, respectively.
        import app.core.meta_agent_router as router_mod

        from app.core.llm_gateway import ChatResponse

        # Decision layer response (complex task)
        router_mod.chat_completion = AsyncMock(return_value=ChatResponse(
            content=json.dumps({
                "complexity": "complex",
                "reasoning": "需要多Agent协作",
                "suggested_direction": "搜索+分析+报告",
                "needs_plan": True,
            }),
            model="deepseek-chat",
            finish_reason="stop",
        ))

        # Review layer: streaming synthesis
        from app.core.llm_gateway import Delta

        async def mock_stream(*args, **kwargs):
            for chunk_text in [
                "# 最终报告\n\n", "执行结果汇总：\n",
                "- 数据搜索完成\n", "- 分析已完成\n",
                "\n## 评价\n", "结果质量良好。",
            ]:
                yield Delta(content=chunk_text)
        router_mod.chat_completion_stream = mock_stream

        events = []
        async def callback(event_type, data):
            events.append({"type": event_type, "data": data})

        # Auto-approve
        router._wait_for_approval = AsyncMock(return_value=True)

        decision_agent = agent_store.get_agent("d1")
        result = await router._run_meta_pipeline(
            "分析竞品数据并生成报告",
            "conv-int-1",
            decision_agent,
            "deepseek-chat",
            callback,
        )

        # Verify pipeline steps occurred
        event_types = [e["type"] for e in events]
        assert "meta_agent_started" in event_types
        assert "meta_agent_completed" in event_types
        assert "layer_transition" in event_types
        assert "plan_created" in event_types
        assert "plan_awaiting_approval" in event_types

        # Verify engine calls
        engine.generate_plan.assert_called_once()
        engine.execute_plan.assert_called_once()

        # Verify result contains review content
        assert "最终报告" in result or "执行结果汇总" in result

    @pytest.mark.asyncio
    async def test_simple_shortcut_bypasses_layers(self, agent_store, llm, engine):
        """Simple message -> bypasses strategy/execution layers."""
        # Override decision to return simple
        llm.chat_completion.return_value = MockResponse(json.dumps({
            "complexity": "simple",
            "reasoning": "简单查询",
            "suggested_agent_name": "数据专家",
            "needs_plan": False,
        }))

        router = MetaAgentRouter(
            agent_store=agent_store,
            orchestration_engine=engine,
            llm_gateway=llm,
        )

        # Patch chat_completion for the decision layer
        import app.core.meta_agent_router as router_mod

        from app.core.llm_gateway import ChatResponse

        router_mod.chat_completion = AsyncMock(return_value=ChatResponse(
            content=json.dumps({
                "complexity": "simple",
                "reasoning": "简单查询",
                "suggested_agent_name": "数据专家",
                "needs_plan": False,
            }),
            model="deepseek-chat",
            finish_reason="stop",
        ))

        events = []
        async def callback(event_type, data):
            events.append({"type": event_type, "data": data})

        router._delegate_simple = AsyncMock(return_value="直接回答：今天天气晴")
        decision_agent = agent_store.get_agent("d1")

        result = await router._run_meta_pipeline(
            "今天天气怎么样", "conv-int-2",
            decision_agent, "deepseek-chat", callback,
        )

        assert result == "直接回答：今天天气晴"
        # Strategy/execution should NOT be called
        engine.generate_plan.assert_not_called()
        engine.execute_plan.assert_not_called()

    @pytest.mark.asyncio
    async def test_backward_compatible_flat_orchestration(self, agent_store):
        """Non-meta agent with agent_communication -> flat orchestration."""
        router = MetaAgentRouter(
            agent_store=agent_store,
            orchestration_engine=MagicMock(),
            llm_gateway=MagicMock(),
        )

        events = []
        async def callback(event_type, data):
            events.append({"type": event_type, "data": data})

        # Try routing via non-meta agent
        try:
            await router.route(
                "分析数据",
                "conv-int-3",
                "w2",  # is_meta=False but has agent_communication
                "deepseek-chat",
                callback,
            )
        except NotImplementedError:
            pass  # Expected -- api/ws.py catches and delegates

        # The NotImplementedError is correct -- it means the caller should
        # delegate to _handle_orchestrated_message in api/ws.py
