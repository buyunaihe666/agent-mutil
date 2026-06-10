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
                    content = data.get("content", "")
                    if not content:
                        continue

                    # Build chat messages for LLM context
                    from app.core.config import get_settings
                    from app.core.llm_gateway import (
                        ChatMessage,
                        ChatRequest,
                        chat_completion_stream,
                    )

                    settings = get_settings()

                    system_prompt = (
                        "You are NEXUS AI, a helpful assistant in a multi-agent collaboration platform. "
                        "You help users with coding, data analysis, research, and creative tasks. "
                        "Respond in Chinese when the user writes in Chinese, otherwise respond in English. "
                        "Be concise but thorough."
                    )

                    messages = [
                        ChatMessage(role="system", content=system_prompt),
                        ChatMessage(role="user", content=content),
                    ]

                    request = ChatRequest(
                        model=f"deepseek/{settings.DEFAULT_LLM_MODEL}",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=4096,
                        stream=True,
                    )

                    # Send "thinking" status
                    await ws_manager.send_to_conversation(
                        conversation_id,
                        ServerMessage(
                            type=MessageType.AGENT_STATUS,
                            conversation_id=conversation_id,
                            status="thinking",
                        ),
                    )

                    try:
                        full_content = ""
                        # Generate a stable message_id so frontend can track this streaming message
                        msg_id = str(uuid.uuid4())
                        async for delta in chat_completion_stream(request):
                            if delta.content:
                                full_content += delta.content
                                await ws_manager.send_to_conversation(
                                    conversation_id,
                                    ServerMessage(
                                        type=MessageType.AGENT_DELTA,
                                        conversation_id=conversation_id,
                                        delta=delta.content,
                                        agent_name="NEXUS AI",
                                        agent_emoji="🤖",
                                        message_id=msg_id,
                                    ),
                                )
                            if delta.finish_reason:
                                break

                        # Send final message with same message_id
                        await ws_manager.send_to_conversation(
                            conversation_id,
                            ServerMessage(
                                type=MessageType.AGENT_MESSAGE,
                                conversation_id=conversation_id,
                                content=full_content,
                                agent_name="NEXUS AI",
                                agent_emoji="🤖",
                                status="complete",
                                message_id=msg_id,
                            ),
                        )

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

                elif msg_type == MessageType.CONFIRM_ACTION:
                    # Placeholder for confirmation logic
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
