"""WebSocket message schemas and connection manager."""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import structlog
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# --- Enums ---

class MessageType(str, Enum):
    USER_MESSAGE = "user_message"
    AGENT_MESSAGE = "agent_message"
    AGENT_DELTA = "agent_delta"
    AGENT_STATUS = "agent_status"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_RESULT = "tool_call_result"
    PLAN_CREATED = "plan_created"
    PLAN_AWAITING_APPROVAL = "plan_awaiting_approval"
    PLAN_APPROVED = "plan_approved"        # client -> server
    PLAN_REJECTED = "plan_rejected"        # client -> server
    PLAN_UPDATED = "plan_updated"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    EXECUTION_PAUSED = "execution_paused"
    EXECUTION_RESUMED = "execution_resumed"
    EXECUTION_CANCELLED = "execution_cancelled"
    RETRY_STEP = "retry_step"              # client -> server
    AGENT_ACTIVITY = "agent_activity"
    AUDIT_EVENTS = "audit_events"
    SYSTEM = "system"
    CONFIRM_ACTION = "confirm_action"
    CONTROL = "control"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    HARDWARE_STATS = "hardware_stats"
    CONTAINER_STATS = "container_stats"

    # Meta-Agent 分层消息
    META_AGENT_STARTED = "meta_agent_started"         # Meta-Agent 开始工作
    META_AGENT_COMPLETED = "meta_agent_completed"     # Meta-Agent 完成工作
    META_AGENT_DISPATCH = "meta_agent_dispatch"       # 执行Agent派发step
    TRIAGE_RESULT = "triage_result"                   # 决策Agent复杂度判断
    LAYER_TRANSITION = "layer_transition"             # 层级切换
    PLAN_SAVED = "plan_saved"                         # Plan 已保存(供审批)

class ControlAction(str, Enum):
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"


class ErrorCode(str, Enum):
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RATE_LIMITED = "RATE_LIMITED"
    MODEL_ERROR = "MODEL_ERROR"
    SANDBOX_ERROR = "SANDBOX_ERROR"
    INVALID_MESSAGE = "INVALID_MESSAGE"
    CONVERSATION_NOT_FOUND = "CONVERSATION_NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# --- Pydantic Schemas ---

class ClientMessage(BaseModel):
    """Message from client to server."""
    type: MessageType
    conversation_id: Optional[str] = None
    content: Optional[str] = None
    agent_id: Optional[str] = None
    action: Optional[str] = None
    data: Optional[dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ServerMessage(BaseModel):
    """Message from server to client."""
    type: MessageType
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    agent_emoji: Optional[str] = None
    content: Optional[str] = None
    delta: Optional[str] = None
    content_blocks: Optional[list[dict]] = None
    status: Optional[str] = None
    token_usage: Optional[dict] = None
    data: Optional[dict] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    recoverable: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# --- Connection Manager ---

class ConnectionManager:
    """Manages WebSocket connections across all endpoints."""

    def __init__(self):
        # Chat connections: conversation_id -> set of WebSocket connections
        self._chat_connections: dict[str, set[WebSocket]] = {}
        # Monitor connections: global set
        self._monitor_connections: set[WebSocket] = set()
        # Agent status connections: global set
        self._agent_connections: set[WebSocket] = set()
        # Lock for thread-safety
        self._lock = asyncio.Lock()

    async def connect_chat(self, websocket: WebSocket, conversation_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            if conversation_id not in self._chat_connections:
                self._chat_connections[conversation_id] = set()
            self._chat_connections[conversation_id].add(websocket)
        logger.info("Chat WebSocket connected", conversation_id=conversation_id)

    async def disconnect_chat(self, websocket: WebSocket, conversation_id: str) -> None:
        async with self._lock:
            if conversation_id in self._chat_connections:
                self._chat_connections[conversation_id].discard(websocket)
                if not self._chat_connections[conversation_id]:
                    del self._chat_connections[conversation_id]
        logger.info("Chat WebSocket disconnected", conversation_id=conversation_id)

    async def connect_monitor(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._monitor_connections.add(websocket)
        logger.info("Monitor WebSocket connected")

    async def disconnect_monitor(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._monitor_connections.discard(websocket)
        logger.info("Monitor WebSocket disconnected")

    async def connect_agent(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._agent_connections.add(websocket)
        logger.info("Agent WebSocket connected")

    async def disconnect_agent(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._agent_connections.discard(websocket)
        logger.info("Agent WebSocket disconnected")

    async def send_to_conversation(self, conversation_id: str, message: ServerMessage) -> None:
        """Send message to all WebSockets watching a conversation."""
        connections = self._chat_connections.get(conversation_id, set()).copy()
        dead: set[WebSocket] = set()
        for ws in connections:
            try:
                await ws.send_text(message.model_dump_json())
            except Exception:
                dead.add(ws)
        for ws in dead:
            await self.disconnect_chat(ws, conversation_id)

    async def broadcast_monitor(self, message: ServerMessage) -> None:
        """Broadcast message to all monitor connections."""
        dead: set[WebSocket] = set()
        for ws in self._monitor_connections.copy():
            try:
                await ws.send_text(message.model_dump_json())
            except Exception:
                dead.add(ws)
        for ws in dead:
            await self.disconnect_monitor(ws)

    async def broadcast_agent_status(self, message: ServerMessage) -> None:
        """Broadcast agent status to all agent connections."""
        dead: set[WebSocket] = set()
        for ws in self._agent_connections.copy():
            try:
                await ws.send_text(message.model_dump_json())
            except Exception:
                dead.add(ws)
        for ws in dead:
            await self.disconnect_agent(ws)

    @property
    def chat_connection_count(self) -> int:
        return sum(len(v) for v in self._chat_connections.values())

    @property
    def monitor_connection_count(self) -> int:
        return len(self._monitor_connections)

    @property
    def agent_connection_count(self) -> int:
        return len(self._agent_connections)

    def get_stats(self) -> dict:
        return {
            "chat_connections": self.chat_connection_count,
            "monitor_connections": self.monitor_connection_count,
            "agent_connections": self.agent_connection_count,
            "active_conversations": list(self._chat_connections.keys()),
        }


# Global singleton
ws_manager = ConnectionManager()
