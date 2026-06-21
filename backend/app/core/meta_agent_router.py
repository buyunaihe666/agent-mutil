"""MetaAgentRouter — 三层 Meta-Agent 调度路由器.

决策层 → 策略层 → 执行层 → 审查
"""

import asyncio
import json as _json
from collections.abc import Callable

import structlog

from app.core.llm_gateway import ChatMessage, ChatRequest, chat_completion, chat_completion_stream

logger = structlog.get_logger(__name__)


class MetaAgentRouter:
    """三层 Meta-Agent 调度路由器"""

    def __init__(self, agent_store, orchestration_engine, llm_gateway):
        self.agent_store = agent_store
        self.orchestration_engine = orchestration_engine
        self.llm_gateway = llm_gateway
        self._approval_callbacks: dict[str, Callable] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def route(
        self, message: str, conversation_id: str,
        orchestrator_agent_id: str, orchestrator_model: str,
        ws_event_callback: Callable,
    ) -> str:
        agent = self.agent_store.get_agent(orchestrator_agent_id)
        if not agent:
            logger.warning("Agent not found", agent_id=orchestrator_agent_id)
            return await self._run_flat_orchestration(
                message, conversation_id,
                {"name": "默认"}, orchestrator_model, ws_event_callback,
            )
        if agent.get("is_meta"):
            return await self._run_meta_pipeline(
                message, conversation_id, agent, orchestrator_model, ws_event_callback,
            )
        else:
            return await self._run_flat_orchestration(
                message, conversation_id, agent, orchestrator_model, ws_event_callback,
            )

    # ------------------------------------------------------------------
    # Meta Pipeline
    # ------------------------------------------------------------------

    async def _run_meta_pipeline(
        self, message: str, conversation_id: str,
        decision_agent: dict, model: str, callback: Callable,
    ) -> str:
        # Layer 1: Decision
        await callback(
            "meta_agent_started", {"layer": "decision", "agent_name": decision_agent["name"]},
        )
        triage = await self._run_decision_layer(message, decision_agent, model)
        await callback("meta_agent_completed", {"layer": "decision", "result": triage})
        await callback("layer_transition", {
            "from_layer": "decision",
            "to_layer": "strategy" if triage["complexity"] == "complex" else "execution",
        })

        if triage["complexity"] == "simple":
            await callback("triage_result", triage)
            return await self._delegate_simple(message, triage, conversation_id, callback)

        await callback("triage_result", triage)

        # Layer 2: Strategy
        strategy_agent = self._get_meta_agent("strategy")
        if not strategy_agent:
            return await self._delegate_simple(message, triage, conversation_id, callback)

        await callback(
            "meta_agent_started", {"layer": "strategy", "agent_name": strategy_agent["name"]},
        )
        plan = await self._run_strategy_layer(triage, strategy_agent, model, conversation_id)
        await callback("plan_created", {"plan_id": plan.plan_id, "title": plan.title})
        await callback(
            "plan_awaiting_approval", {"plan_id": plan.plan_id, "title": plan.title},
        )

        approved = await self._wait_for_approval(plan.plan_id)
        if not approved:
            await callback(
                "meta_agent_completed",
                {"layer": "strategy", "status": "rejected", "plan_id": plan.plan_id},
            )
            return "计划未被批准，已取消执行。"

        await callback("plan_approved", {"plan_id": plan.plan_id})
        await callback(
            "meta_agent_completed", {"layer": "strategy", "plan_id": plan.plan_id},
        )

        # Layer 3: Execution
        execution_agent = self._get_meta_agent("execution") or {
            "name": "执行调度", "is_meta": True,
        }
        await callback(
            "meta_agent_started", {"layer": "execution", "agent_name": execution_agent["name"]},
        )
        await callback("layer_transition", {"from_layer": "strategy", "to_layer": "execution"})
        results = await self._run_execution_layer(plan, execution_agent, callback)
        await callback(
            "meta_agent_completed", {"layer": "execution", "step_count": len(results)},
        )

        # Review
        await callback(
            "meta_agent_started",
            {"layer": "strategy_review", "agent_name": strategy_agent["name"]},
        )
        synthesis = await self._run_review_layer(
            plan, results, strategy_agent, model, conversation_id,
        )
        await callback("meta_agent_completed", {"layer": "strategy_review"})

        return synthesis

    # ------------------------------------------------------------------
    # Layer implementations
    # ------------------------------------------------------------------

    async def _run_decision_layer(self, message: str, decision_agent: dict, model: str) -> dict:
        decision_prompt = (
            "请分析以下用户消息，判断任务复杂度并返回JSON决策结果：\n\n" + message
        )
        messages = [
            ChatMessage(role="system", content=decision_agent.get("system_prompt", "")),
            ChatMessage(role="user", content=decision_prompt),
        ]
        try:
            response = await chat_completion(ChatRequest(
                model=model, messages=messages,
                temperature=decision_agent.get("temperature", 0.3),
                max_tokens=decision_agent.get("max_tokens", 4096),
            ))
            content = response.content.strip() if response.content else ""
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])
            result = _json.loads(content)
            return {
                "complexity": result.get("complexity", "simple"),
                "reasoning": result.get("reasoning", ""),
                "suggested_direction": result.get("suggested_direction"),
                "suggested_agent_name": result.get("suggested_agent_name"),
                "needs_plan": result.get("needs_plan", False),
            }
        except Exception as e:
            logger.warning("Decision layer failed, fallback to simple", error=str(e))
            return {
                "complexity": "simple",
                "reasoning": f"决策层异常: {e}",
                "suggested_agent_name": None,
                "needs_plan": False,
            }

    async def _run_strategy_layer(
        self, triage: dict, strategy_agent: dict, model: str, conversation_id: str,
    ):
        all_agents, _ = await self.agent_store.list_agents()
        available_agents = [a for a in all_agents if not a.get("is_meta")]
        direction = triage.get("suggested_direction", "") or triage.get("reasoning", "")
        plan = await self.orchestration_engine.generate_plan(
            user_content=direction,
            available_agents=available_agents,
            orchestrator_model=model,
        )
        return plan

    async def _run_execution_layer(
        self, plan, execution_agent: dict, callback: Callable,
    ) -> list:
        results = await self.orchestration_engine.execute_plan(
            plan_id=plan.plan_id, on_event=callback,
        )
        return results

    async def _run_review_layer(
        self, plan, results: list, strategy_agent: dict,
        model: str, conversation_id: str,
    ) -> str:
        results_text = "\n".join([
            f"- Step {r.step_id}: status={r.status}, output={r.output or 'N/A'}"
            for r in results
        ])
        review_system = (
            "你是一个审查者。请根据执行结果生成最终总结。"
            "评估结果质量，指出亮点和不足。"
        )
        review_user = (
            f"Plan: {plan.title}\n\n"
            f"执行结果：\n{results_text}\n\n"
            "请生成最终总结报告。"
        )
        messages = [
            ChatMessage(role="system", content=review_system),
            ChatMessage(role="user", content=review_user),
        ]
        full_content = ""
        async for delta in chat_completion_stream(ChatRequest(
            model=model, messages=messages,
            temperature=0.3, max_tokens=strategy_agent.get("max_tokens", 4096),
        )):
            if delta.content:
                full_content += delta.content
        return full_content

    async def _delegate_simple(
        self, message: str, triage: dict, conversation_id: str, callback: Callable,
    ) -> str:
        suggested_name = triage.get("suggested_agent_name")
        if suggested_name:
            all_agents, _ = await self.agent_store.list_agents()
            for a in all_agents:
                if a.get("name") == suggested_name and not a.get("is_meta"):
                    await callback("meta_agent_dispatch", {
                        "target_agent_id": a["id"],
                        "target_agent_name": a["name"],
                        "message": message,
                    })
                    return await self._run_flat_orchestration(
                        message, conversation_id, a,
                        a.get("default_model", "deepseek-chat"), callback,
                    )
        return await self._run_flat_orchestration(
            message, conversation_id, {"name": "默认"}, "deepseek-chat", callback,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_meta_agent(self, agent_type: str) -> dict | None:
        all_agents = list(self.agent_store.agents.values())
        type_keywords = {"decision": ["决策"], "strategy": ["策略"], "execution": ["执行"]}
        keywords = type_keywords.get(agent_type, [agent_type])
        for agent in all_agents:
            if agent.get("is_meta") and any(k in agent.get("name", "") for k in keywords):
                return agent
        return None

    async def _wait_for_approval(self, plan_id: str) -> bool:
        event = asyncio.Event()
        approved = False

        def on_approval(data: dict):
            nonlocal approved
            if data.get("plan_id") == plan_id:
                approved = data.get("action") == "approve"
                event.set()

        self._approval_callbacks[plan_id] = on_approval
        try:
            await asyncio.wait_for(event.wait(), timeout=300)
        except TimeoutError:
            logger.warning("Plan approval timeout", plan_id=plan_id)
        finally:
            self._approval_callbacks.pop(plan_id, None)
        return approved

    def handle_approval(self, plan_id: str, action: str):
        cb = self._approval_callbacks.get(plan_id)
        if cb:
            cb({"plan_id": plan_id, "action": action})

    async def _run_flat_orchestration(
        self, message: str, conversation_id: str,
        agent: dict, model: str, callback: Callable,
    ) -> str:
        raise NotImplementedError(
            "Flat orchestration is handled by api/ws.py _handle_orchestrated_message"
        )


meta_agent_router: MetaAgentRouter | None = None
