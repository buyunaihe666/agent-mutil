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
                    await ws_manager.send_to_conversation(
                        conversation_id,
                        ServerMessage(
                            type=MessageType.SYSTEM,
                            conversation_id=conversation_id,
                            content=f"Control action received: {action}",
                        ),
                    )

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

    # --- Tool-calling loop ---
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


# --- Monitor WebSocket ---

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
