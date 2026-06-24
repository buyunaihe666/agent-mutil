"""WebSocket endpoints for NEXUS AI."""

import asyncio
import json
import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.ws import (
    ControlAction,
    ErrorCode,
    MessageType,
    ServerMessage,
    ws_manager,
)

logger = structlog.get_logger(__name__)

router = APIRouter()

HEARTBEAT_INTERVAL = 30
PING_TIMEOUT = 90
MAX_TOOL_ROUNDS = 3


# --- Chat WebSocket ---

@router.websocket("/ws/chat/{conversation_id}")
async def ws_chat(websocket: WebSocket, conversation_id: str):
    await ws_manager.connect_chat(websocket, conversation_id)

    heartbeat_task = asyncio.create_task(_heartbeat(websocket, conversation_id))

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                msg_type = data.get("type", "")

                if msg_type == MessageType.PING:
                    await websocket.send_text(ServerMessage(
                        type=MessageType.PONG,
                        conversation_id=conversation_id,
                    ).model_dump_json())

                elif msg_type == MessageType.USER_MESSAGE:
                    await _handle_user_message(conversation_id, data)

                elif msg_type == MessageType.CONFIRM_ACTION:
                    await ws_manager.send_to_conversation(
                        conversation_id,
                        ServerMessage(
                            type=MessageType.SYSTEM,
                            conversation_id=conversation_id,
                            content="Action confirmed.",
                        ),
                    )

                elif msg_type == MessageType.CONTROL:
                    action = data.get("action", "")
                    plan_id = data.get("plan_id", "")
                    if action and plan_id:
                        await _handle_control_action(conversation_id, action, plan_id)
                    else:
                        await ws_manager.send_to_conversation(
                            conversation_id,
                            ServerMessage(
                                type=MessageType.SYSTEM,
                                conversation_id=conversation_id,
                                content=f"Control action received: {action}",
                            ),
                        )

                elif msg_type == MessageType.PLAN_APPROVED:
                    plan_id = data.get("plan_id", "")
                    if plan_id:
                        # Notify MetaAgentRouter of approval
                        try:
                            from app.core.meta_agent_router import meta_agent_router as _mar
                            if _mar:
                                _mar.handle_approval(plan_id, "approve")
                        except Exception:
                            pass
                        asyncio.create_task(_execute_approved_plan(conversation_id, plan_id))

                elif msg_type == MessageType.PLAN_REJECTED:
                    plan_id = data.get("plan_id", "")
                    if plan_id:
                        # Notify MetaAgentRouter of rejection
                        try:
                            from app.core.meta_agent_router import meta_agent_router as _mar
                            if _mar:
                                _mar.handle_approval(plan_id, "reject")
                        except Exception:
                            pass
                        from app.core.orchestration_engine import orchestration_engine
                        await orchestration_engine.cancel(plan_id)
                        await ws_manager.send_to_conversation(
                            conversation_id,
                            ServerMessage(
                                type=MessageType.EXECUTION_CANCELLED,
                                conversation_id=conversation_id,
                                data={"plan_id": plan_id},
                            ),
                        )

                elif msg_type == MessageType.RETRY_STEP:
                    plan_id = data.get("plan_id", "")
                    step_id = data.get("step_id", "")
                    if plan_id and step_id:
                        asyncio.create_task(_handle_retry_step(conversation_id, plan_id, step_id))

                else:
                    await websocket.send_text(ServerMessage(
                        type=MessageType.ERROR,
                        conversation_id=conversation_id,
                        error_code="INVALID_MESSAGE",
                        error_message=f"Unknown message type: {msg_type}",
                        recoverable=True,
                    ).model_dump_json())

            except json.JSONDecodeError:
                await websocket.send_text(ServerMessage(
                    type=MessageType.ERROR,
                    conversation_id=conversation_id,
                    error_code="INVALID_MESSAGE",
                    error_message="Invalid JSON format",
                    recoverable=True,
                ).model_dump_json())

    except WebSocketDisconnect:
        logger.info("Chat WebSocket client disconnected", conversation_id=conversation_id)
    except Exception as e:
        logger.error("Chat WebSocket error", conversation_id=conversation_id, error=str(e))
    finally:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        await ws_manager.disconnect_chat(websocket, conversation_id)


async def _handle_user_message(conversation_id: str, data: dict) -> None:
    """Handle a user_message from the client with agent_id, history, and tool calling."""
    content = data.get("content", "")
    if not content:
        return

    from app.core.agent_service import agent_store
    from app.core.config import get_settings
    from app.core.conversation_service import MessageCreate, conversation_store
    from app.core.llm_gateway import (
        ChatMessage,
        ChatRequest,
        chat_completion_stream,
    )
    from app.core.tool_registry import tool_registry

    settings = get_settings()

    # --- Load agent configuration ---
    agent_id = data.get("agent_id")
    agent_name = "NEXUS AI"
    agent_emoji = "🤖"
    system_prompt = (
        "You are NEXUS AI, a helpful assistant in a multi-agent collaboration platform. "
        "You help users with coding, data analysis, research, and creative tasks. "
        "Respond in Chinese when the user writes in Chinese, otherwise respond in English. "
        "Be concise but thorough."
    )
    temperature = 0.7
    max_tokens = 4096
    model = settings.DEFAULT_LLM_MODEL
    agent_tools: list[str] = []

    if agent_id:
        agent = await agent_store.get_agent(agent_id)
        if agent:
            agent_name = agent.get("name", "NEXUS AI")
            agent_emoji = agent.get("avatar_emoji", "🤖")
            system_prompt = agent.get("system_prompt") or system_prompt
            temperature = agent.get("temperature", 0.7)
            max_tokens = agent.get("max_tokens", 4096)
            model = agent.get("default_model", settings.DEFAULT_LLM_MODEL)
            agent_tools = agent.get("tools") or []
            logger.info(
                "Agent loaded for chat",
                agent_id=agent_id,
                agent_name=agent_name,
                tools=agent_tools,
            )

    # --- Build messages with conversation history ---
    messages: list[ChatMessage] = [
        ChatMessage(role="system", content=system_prompt),
    ]

    # Add conversation history (last 20 messages)
    try:
        history = await conversation_store.build_context(
            conversation_id, agent_id=agent_id, max_tokens=6000
        )
        for h in history[-20:]:
            role = h.get("role", "user")
            # Map "agent" role to "assistant" for LLM context
            if role == "agent":
                role = "assistant"
            messages.append(ChatMessage(
                role=role,
                content=h.get("content"),
            ))
    except Exception as e:
        logger.warning("Failed to load conversation history", error=str(e))

    # Add current user message
    messages.append(ChatMessage(role="user", content=content))

    # --- Persist user message ---
    try:
        await conversation_store.add_message(conversation_id, MessageCreate(
            role="user",
            content=content,
            agent_id=agent_id,
        ))
    except Exception as e:
        logger.warning("Failed to persist user message", error=str(e))

    # --- Prepare tools ---
    tools = None
    if agent_tools:
        tools = tool_registry.get_function_definitions(agent_tools)
        if not tools:
            tools = None  # Don't pass empty list

    # --- Send "thinking" status ---
    await ws_manager.send_to_conversation(
        conversation_id,
        ServerMessage(
            type=MessageType.AGENT_STATUS,
            conversation_id=conversation_id,
            agent_name=agent_name,
            agent_emoji=agent_emoji,
            status="thinking",
        ),
    )

    # --- Log audit event for user message ---
    from app.core.monitor_service import AgentActivity, AgentActivityStatus, monitor_service
    from app.core.security import audit_logger
    if agent_id:
        try:
            audit_logger.log(
                action_type="send_message",
                resource_type="conversation",
                resource_id=conversation_id,
                agent_id=agent_id,
            )
            await monitor_service.update_agent_activity(AgentActivity(
                agent_id=agent_id,
                agent_name=agent_name,
                agent_emoji=agent_emoji,
                status=AgentActivityStatus.WORKING,
                message="正在处理用户请求...",
                conversation_id=conversation_id,
            ))
            await monitor_service.push_stats_via_ws(ws_manager)
        except Exception as e:
            logger.warning("Failed to push monitor activity", error=str(e))

    # --- Check if this is an orchestrator agent ---
    is_orchestrator = "agent_communication" in agent_tools
    if is_orchestrator and agent_id:
        # Check if this is a Meta-Agent (new three-layer path)
        from app.core.meta_agent_router import meta_agent_router as _meta_router
        agent = agent_store.get_agent(agent_id)
        if agent and agent.get("is_meta") and _meta_router:
            # Meta-Agent → three-layer pipeline
            async def _meta_callback(event_type: str, data: dict):
                """Bridge MetaAgentRouter events to WebSocket messages."""
                try:
                    await ws_manager.send_to_conversation(conversation_id, ServerMessage(
                        type=MessageType(event_type) if event_type in [e.value for e in MessageType] else MessageType.SYSTEM,
                        conversation_id=conversation_id,
                        agent_name=data.get("agent_name", agent_name),
                        agent_emoji=data.get("agent_emoji", agent_emoji),
                        data=data,
                    ))
                except Exception as cb_err:
                    logger.warning("Meta callback failed", error=str(cb_err))

            try:
                full_content = await _meta_router.route(
                    message=content,
                    conversation_id=conversation_id,
                    orchestrator_agent_id=agent_id,
                    orchestrator_model=model,
                    ws_event_callback=_meta_callback,
                )
            except NotImplementedError:
                # Fallback to flat orchestration
                full_content = await _handle_orchestrated_message(
                    conversation_id=conversation_id,
                    user_content=content,
                    agent_id=agent_id,
                    agent_name=agent_name,
                    agent_emoji=agent_emoji,
                    model=model,
                )
            except Exception as meta_err:
                logger.error("MetaAgentRouter failed, fallback to flat", error=str(meta_err))
                full_content = await _handle_orchestrated_message(
                    conversation_id=conversation_id,
                    user_content=content,
                    agent_id=agent_id,
                    agent_name=agent_name,
                    agent_emoji=agent_emoji,
                    model=model,
                )
        else:
            # Existing flat orchestration flow (backward compatible)
            full_content = await _handle_orchestrated_message(
                conversation_id=conversation_id,
                user_content=content,
                agent_id=agent_id,
                agent_name=agent_name,
                agent_emoji=agent_emoji,
                model=model,
            )
    else:
        # Single-agent tool-calling flow
        msg_id = str(uuid.uuid4())
        try:
            full_content = await _stream_with_tools(
                conversation_id=conversation_id,
                messages=messages,
                tools=tools,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                agent_name=agent_name,
                agent_emoji=agent_emoji,
                msg_id=msg_id,
            )

            # Send final message
            await ws_manager.send_to_conversation(
                conversation_id,
                ServerMessage(
                    type=MessageType.AGENT_MESSAGE,
                    conversation_id=conversation_id,
                    content=full_content,
                    agent_name=agent_name,
                    agent_emoji=agent_emoji,
                    status="complete",
                    message_id=msg_id,
                ),
            )

            # --- Persist assistant message ---
            if full_content:
                try:
                    await conversation_store.add_message(conversation_id, MessageCreate(
                        role="assistant",
                        content=full_content,
                        agent_id=agent_id,
                    ))
                except Exception as e:
                    logger.warning("Failed to persist assistant message", error=str(e))

        except Exception as e:
            logger.error("LLM call failed", error=str(e))
            await ws_manager.send_to_conversation(
                conversation_id,
                ServerMessage(
                    type=MessageType.ERROR,
                    conversation_id=conversation_id,
                    error_code=ErrorCode.MODEL_ERROR,
                    error_message=f"AI response failed: {str(e)}",
                    recoverable=True,
                ),
            )
    if agent_id:
        try:
            await monitor_service.update_agent_activity(AgentActivity(
                agent_id=agent_id,
                agent_name=agent_name,
                agent_emoji=agent_emoji,
                status=AgentActivityStatus.IDLE,
                message="已完成处理",
                conversation_id=conversation_id,
            ))
            await monitor_service.push_stats_via_ws(ws_manager)
        except Exception as e:
            logger.warning("Failed to update agent activity", error=str(e))


async def _stream_with_tools(
    *,
    conversation_id: str,
    messages: list,
    tools: list[dict] | None,
    model: str,
    temperature: float,
    max_tokens: int,
    agent_name: str,
    agent_emoji: str,
    msg_id: str,
) -> str:
    """Stream an LLM response, handling tool calls with up to MAX_TOOL_ROUNDS recursion."""

    from app.core.llm_gateway import (
        ChatMessage,
        ChatRequest,
        chat_completion_stream,
    )
    from app.core.tool_registry import tool_registry

    full_content = ""
    remaining_rounds = MAX_TOOL_ROUNDS

    while remaining_rounds > 0:
        remaining_rounds -= 1

        request = ChatRequest(
            model=f"deepseek/{model}",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools if remaining_rounds == MAX_TOOL_ROUNDS - 1 else tools,
            stream=True,
        )

        # Accumulate tool call deltas by index
        tool_call_accumulator: dict[int, dict] = {}
        content_this_round = ""
        finish_reason: str | None = None

        async for delta in chat_completion_stream(request):
            if delta.tool_call_delta:
                idx = delta.tool_call_delta.get("index", 0)
                if idx not in tool_call_accumulator:
                    tool_call_accumulator[idx] = {
                        "id": "",
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                    }
                tc = tool_call_accumulator[idx]
                if delta.tool_call_delta.get("id"):
                    tc["id"] = delta.tool_call_delta["id"]
                if delta.tool_call_delta.get("function", {}).get("name"):
                    tc["function"]["name"] += delta.tool_call_delta["function"]["name"]
                if delta.tool_call_delta.get("function", {}).get("arguments"):
                    tc["function"]["arguments"] += delta.tool_call_delta["function"]["arguments"]

            if delta.content:
                content_this_round += delta.content
                full_content += delta.content
                await ws_manager.send_to_conversation(
                    conversation_id,
                    ServerMessage(
                        type=MessageType.AGENT_DELTA,
                        conversation_id=conversation_id,
                        delta=delta.content,
                        agent_name=agent_name,
                        agent_emoji=agent_emoji,
                        message_id=msg_id,
                    ),
                )

            if delta.finish_reason:
                finish_reason = delta.finish_reason
                if finish_reason == "tool_calls":
                    break
                elif finish_reason == "stop":
                    break
                elif finish_reason == "length":
                    break

        # If no tool calls, we're done
        if not tool_call_accumulator or finish_reason != "tool_calls":
            return full_content

        # --- Execute tool calls ---
        tool_calls = list(tool_call_accumulator.values())

        # Add assistant message with tool_calls to conversation
        messages.append(ChatMessage(
            role="assistant",
            content=content_this_round if content_this_round else None,
            tool_calls=tool_calls,
        ))

        for tc in tool_calls:
            tool_name = tc["function"]["name"]
            tool_args_str = tc["function"]["arguments"]

            # Parse tool arguments (handle possible JSON errors)
            try:
                tool_args = json.loads(tool_args_str) if tool_args_str else {}
            except json.JSONDecodeError:
                tool_args = {}

            # Notify frontend: tool call started
            await ws_manager.send_to_conversation(
                conversation_id,
                ServerMessage(
                    type=MessageType.TOOL_CALL_START,
                    conversation_id=conversation_id,
                    agent_name=agent_name,
                    agent_emoji=agent_emoji,
                    data={
                        "tool_call_id": tc["id"],
                        "name": tool_name,
                        "arguments": tool_args,
                    },
                ),
            )

            # Execute the tool
            try:
                result = await tool_registry.execute_tool(tool_name, **tool_args)
            except Exception as exc:
                result = type("ToolResult", (), {
                    "success": False,
                    "output": "",
                    "error": str(exc),
                })()

            # Notify frontend: tool call result
            await ws_manager.send_to_conversation(
                conversation_id,
                ServerMessage(
                    type=MessageType.TOOL_CALL_RESULT,
                    conversation_id=conversation_id,
                    agent_name=agent_name,
                    agent_emoji=agent_emoji,
                    data={
                        "tool_call_id": tc["id"],
                        "name": tool_name,
                        "success": result.success,
                        "output": result.output,
                        "error": result.error,
                    },
                ),
            )

            # Add tool result to conversation
            tool_result_content = result.output if result.success else f"Error: {result.error}"
            messages.append(ChatMessage(
                role="tool",
                content=tool_result_content,
                tool_call_id=tc["id"],
                name=tool_name,
            ))

        # Continue loop — call LLM again with tool results
        logger.info(
            "Tool calls executed, continuing LLM loop",
            remaining_rounds=remaining_rounds,
            tool_count=len(tool_calls),
        )

    # Exhausted tool rounds — return whatever content we have
    return full_content


async def _handle_orchestrated_message(
    *,
    conversation_id: str,
    user_content: str,
    agent_id: str,
    agent_name: str,
    agent_emoji: str,
    model: str,
) -> str:
    """Handle a message through the orchestration engine.

    Uses OrchestrationEngine.generate_plan() for LLM-driven task decomposition
    and execute_plan() with an event callback for WebSocket notifications.
    The engine is the single source of truth for both plan creation and execution.
    """
    from app.core.agent_service import agent_store as _agent_store
    from app.core.llm_gateway import ChatMessage, ChatRequest, chat_completion_stream
    from app.core.orchestration_engine import orchestration_engine

    full_content = ""
    msg_id = str(uuid.uuid4())

    # Step 1: Build available agent list (exclude orchestrator)
    all_agents, _ = await _agent_store.list_agents()
    available_agents = [a for a in all_agents if a.get("id") != agent_id]

    # Step 2: Generate plan via engine (LLM decomposition)
    try:
        plan = await orchestration_engine.generate_plan(
            user_content=user_content,
            available_agents=available_agents,
            orchestrator_model=model,
        )
    except Exception as e:
        logger.error("Failed to generate orchestration plan", error=str(e))
        return await _fallback_single_response(
            conversation_id, user_content, agent_name, agent_emoji, msg_id,
        )

    # Step 3: Build plan_steps for frontend
    plan_steps = []
    for st in plan.subtasks:
        assigned = None
        for a in all_agents:
            if a.get("id") == st.assigned_agent_id:
                assigned = a
                break
        plan_steps.append({
            "step_id": st.step_id,
            "description": st.description,
            "agent_name": st.assigned_agent_name or "未分配",
            "agent_emoji": assigned.get("avatar_emoji", "🤖") if assigned else "🤖",
            "status": "pending",
        })

    # Step 4: Send plan to frontend
    await ws_manager.send_to_conversation(conversation_id, ServerMessage(
        type=MessageType.PLAN_CREATED,
        conversation_id=conversation_id,
        agent_name=agent_name,
        agent_emoji=agent_emoji,
        message_id=msg_id,
        data={
            "plan_id": plan.plan_id,
            "title": plan.title,
            "steps": plan_steps,
        },
    ))

    # Step 5: Execute plan with WebSocket event callback
    async def ws_event_callback(event_type: str, plan_id: str, data: dict | None) -> None:
        """Relay orchestration events to the frontend via WebSocket."""
        data = data or {}
        msg_type_map = {
            "step_started": MessageType.STEP_STARTED,
            "step_completed": MessageType.STEP_COMPLETED,
            "step_failed": MessageType.STEP_FAILED,
        }
        if event_type in msg_type_map:
            await ws_manager.send_to_conversation(conversation_id, ServerMessage(
                type=msg_type_map[event_type],
                conversation_id=conversation_id,
                agent_name=agent_name,
                agent_emoji=agent_emoji,
                message_id=msg_id,
                data={
                    "step_id": data.get("step_id", ""),
                    "plan_id": plan_id,
                    "output": data.get("output", ""),
                    "error": data.get("error", ""),
                },
            ))

    try:
        results = await orchestration_engine.execute_plan(
            plan.plan_id,
            on_event=ws_event_callback,
        )
    except Exception as e:
        logger.error("Plan execution failed", plan_id=plan.plan_id, error=str(e))
        return await _fallback_single_response(
            conversation_id, user_content, agent_name, agent_emoji, msg_id,
        )

    # Step 6: Synthesize final response from step results
    synthesis_parts = []
    for i, st in enumerate(plan.subtasks):
        result = results[i] if i < len(results) else None
        output = result.output if result else ''
        agent_label = st.assigned_agent_name or "Agent"
        synthesis_parts.append(f"### {agent_label}: {st.description}\n\n{output}")

    synthesis_prompt = (
        "你是一个任务协调者。以下是各个工作智能体完成子任务的结果。"
        "请整合这些结果，输出一个统一、连贯的最终回复。\n\n"
        "## 原始用户任务\n" + user_content + "\n\n"
        "## 子任务结果\n\n" + "\n\n---\n\n".join(synthesis_parts) + "\n\n"
        "## 要求\n"
        "1. 先用2-3句话总结整体结论\n"
        "2. 按逻辑顺序展开详细内容\n"
        "3. 使用Markdown格式\n"
        "4. 标注不确定的内容"
    )

    # Stream the synthesis
    try:
        request = ChatRequest(
            model=f"deepseek/{model}",
            messages=[ChatMessage(role="user", content=synthesis_prompt)],
            temperature=0.5,
            max_tokens=4096,
            stream=True,
        )
        async for delta in chat_completion_stream(request):
            if delta.content:
                full_content += delta.content
                await ws_manager.send_to_conversation(
                    conversation_id,
                    ServerMessage(
                        type=MessageType.AGENT_DELTA,
                        conversation_id=conversation_id,
                        delta=delta.content,
                        agent_name=agent_name,
                        agent_emoji=agent_emoji,
                        message_id=msg_id,
                    ),
                )
            if delta.finish_reason:
                break
    except Exception as e:
        logger.error("Synthesis failed", error=str(e))
        if not full_content:
            full_content = "任务已完成。以下是各智能体的执行结果：\n\n" + "\n\n---\n\n".join(synthesis_parts)

    return full_content


async def _fallback_single_response(
    conversation_id: str,
    content: str,
    agent_name: str,
    agent_emoji: str,
    msg_id: str,
) -> str:
    """Fallback to single-agent response when orchestration fails."""
    from app.core.config import get_settings
    from app.core.llm_gateway import ChatMessage, ChatRequest, chat_completion_stream

    settings = get_settings()
    full = ""
    try:
        request = ChatRequest(
            model=f"deepseek/{settings.DEFAULT_LLM_MODEL}",
            messages=[
                ChatMessage(role="system", content="你是NEXUS AI平台的智能助理。"),
                ChatMessage(role="user", content=content),
            ],
            temperature=0.7,
            max_tokens=4096,
            stream=True,
        )
        async for delta in chat_completion_stream(request):
            if delta.content:
                full += delta.content
                await ws_manager.send_to_conversation(
                    conversation_id,
                    ServerMessage(
                        type=MessageType.AGENT_DELTA,
                        conversation_id=conversation_id,
                        delta=delta.content,
                        agent_name=agent_name,
                        agent_emoji=agent_emoji,
                        message_id=msg_id,
                    ),
                )
            if delta.finish_reason:
                break
    except Exception:
        full = "抱歉，处理您请求时遇到了问题。请稍后重试。"
    return full

@router.websocket("/ws/monitor")
async def ws_monitor(websocket: WebSocket):
    await ws_manager.connect_monitor(websocket)

    heartbeat_task = asyncio.create_task(_heartbeat(websocket))

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "")

            if msg_type == MessageType.PING:
                await websocket.send_text(ServerMessage(
                    type=MessageType.PONG,
                ).model_dump_json())

    except WebSocketDisconnect:
        logger.info("Monitor WebSocket client disconnected")
    except Exception as e:
        logger.error("Monitor WebSocket error", error=str(e))
    finally:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        await ws_manager.disconnect_monitor(websocket)


# --- Agent Status WebSocket ---

@router.websocket("/ws/agents")
async def ws_agents(websocket: WebSocket):
    await ws_manager.connect_agent(websocket)

    heartbeat_task = asyncio.create_task(_heartbeat(websocket))

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "")

            if msg_type == MessageType.PING:
                await websocket.send_text(ServerMessage(
                    type=MessageType.PONG,
                ).model_dump_json())

    except WebSocketDisconnect:
        logger.info("Agent WebSocket client disconnected")
    except Exception as e:
        logger.error("Agent WebSocket error", error=str(e))
    finally:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        await ws_manager.disconnect_agent(websocket)


async def _heartbeat(websocket: WebSocket, conversation_id: str | None = None) -> None:
    """Send periodic ping to WebSocket client."""
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            try:
                await websocket.send_text(ServerMessage(
                    type=MessageType.PING,
                    conversation_id=conversation_id,
                ).model_dump_json())
            except Exception:
                break
    except asyncio.CancelledError:
        pass


async def _handle_control_action(conversation_id: str, action: str, plan_id: str) -> None:
    """Handle pause/resume/cancel control actions for an orchestration plan."""
    from app.core.orchestration_engine import orchestration_engine

    try:
        if action == ControlAction.PAUSE:
            success = await orchestration_engine.pause(plan_id)
            if success:
                await ws_manager.send_to_conversation(
                    conversation_id,
                    ServerMessage(
                        type=MessageType.EXECUTION_PAUSED,
                        conversation_id=conversation_id,
                        data={"plan_id": plan_id},
                    ),
                )
        elif action == ControlAction.RESUME:
            success = await orchestration_engine.resume(plan_id)
            if success:
                await ws_manager.send_to_conversation(
                    conversation_id,
                    ServerMessage(
                        type=MessageType.EXECUTION_RESUMED,
                        conversation_id=conversation_id,
                        data={"plan_id": plan_id},
                    ),
                )
        elif action == ControlAction.CANCEL:
            success = await orchestration_engine.cancel(plan_id)
            if success:
                await ws_manager.send_to_conversation(
                    conversation_id,
                    ServerMessage(
                        type=MessageType.EXECUTION_CANCELLED,
                        conversation_id=conversation_id,
                        data={"plan_id": plan_id},
                    ),
                )
        else:
            await ws_manager.send_to_conversation(
                conversation_id,
                ServerMessage(
                    type=MessageType.ERROR,
                    conversation_id=conversation_id,
                    error_code="INVALID_ACTION",
                    error_message=f"Unknown control action: {action}",
                    recoverable=True,
                ),
            )
    except Exception as e:
        logger.error("Control action failed", action=action, plan_id=plan_id, error=str(e))
        await ws_manager.send_to_conversation(
            conversation_id,
            ServerMessage(
                type=MessageType.ERROR,
                conversation_id=conversation_id,
                error_code="CONTROL_FAILED",
                error_message=f"Control action {action} failed: {str(e)}",
                recoverable=True,
            ),
        )


async def _execute_approved_plan(conversation_id: str, plan_id: str) -> None:
    """Execute a plan that has been approved by the user."""
    from app.core.llm_gateway import ChatMessage, ChatRequest, chat_completion_stream
    from app.core.orchestration_engine import orchestration_engine

    plan = orchestration_engine.get_plan(plan_id)
    if not plan:
        return

    msg_id = str(uuid.uuid4())
    full_content = ""

    # Use the event callback from the plan's original handling
    async def ws_callback(event_type: str, _plan_id: str, data: dict | None) -> None:
        data = data or {}
        msg_type_map = {
            "step_started": MessageType.STEP_STARTED,
            "step_completed": MessageType.STEP_COMPLETED,
            "step_failed": MessageType.STEP_FAILED,
        }
        if event_type in msg_type_map:
            await ws_manager.send_to_conversation(conversation_id, ServerMessage(
                type=msg_type_map[event_type],
                conversation_id=conversation_id,
                data={
                    "step_id": data.get("step_id", ""),
                    "plan_id": plan_id,
                    "output": data.get("output", ""),
                    "error": data.get("error", ""),
                },
            ))

    try:
        results = await orchestration_engine.execute_plan(plan_id, on_event=ws_callback)
    except Exception as e:
        logger.error("Approved plan execution failed", plan_id=plan_id, error=str(e))
        return

    # Synthesize final response
    synthesis_parts = []
    for i, st in enumerate(plan.subtasks):
        result = results[i] if i < len(results) else None
        output = result.output if result else ''
        agent_label = st.assigned_agent_name or "Agent"
        synthesis_parts.append(f"### {agent_label}: {st.description}\n\n{output}")

    synthesis_prompt = (
        "你是一个任务协调者。以下是各个工作智能体完成子任务的结果。"
        "请整合这些结果，输出一个统一、连贯的最终回复。\n\n"
        "## 子任务结果\n\n" + "\n\n---\n\n".join(synthesis_parts) + "\n\n"
        "## 要求\n"
        "1. 先用2-3句话总结整体结论\n"
        "2. 按逻辑顺序展开详细内容\n"
        "3. 使用Markdown格式\n"
        "4. 标注不确定的内容"
    )

    try:
        request = ChatRequest(
            model=f"deepseek/deepseek-chat",
            messages=[ChatMessage(role="user", content=synthesis_prompt)],
            temperature=0.5,
            max_tokens=4096,
            stream=True,
        )
        async for delta in chat_completion_stream(request):
            if delta.content:
                full_content += delta.content
                await ws_manager.send_to_conversation(
                    conversation_id,
                    ServerMessage(
                        type=MessageType.AGENT_DELTA,
                        conversation_id=conversation_id,
                        delta=delta.content,
                        message_id=msg_id,
                    ),
                )
            if delta.finish_reason:
                break
    except Exception as e:
        logger.error("Synthesis after approval failed", error=str(e))
        if not full_content:
            full_content = "任务已完成。执行结果如上。"


async def _handle_retry_step(conversation_id: str, plan_id: str, step_id: str) -> None:
    """Retry a failed step in an orchestration plan."""
    from app.core.orchestration_engine import orchestration_engine

    try:
        result = await orchestration_engine.retry_step(plan_id, step_id)
        msg_type = MessageType.STEP_COMPLETED if result.status == StepStatus.COMPLETED else MessageType.STEP_FAILED
        await ws_manager.send_to_conversation(
            conversation_id,
            ServerMessage(
                type=msg_type,
                conversation_id=conversation_id,
                data={
                    "step_id": step_id,
                    "plan_id": plan_id,
                    "output": result.output or "",
                    "error": result.error or "",
                },
            ),
        )
    except Exception as e:
        logger.error("Step retry failed", plan_id=plan_id, step_id=step_id, error=str(e))
        await ws_manager.send_to_conversation(
            conversation_id,
            ServerMessage(
                type=MessageType.ERROR,
                conversation_id=conversation_id,
                error_code="RETRY_FAILED",
                error_message=f"Step retry failed: {str(e)}",
                recoverable=True,
            ),
        )
