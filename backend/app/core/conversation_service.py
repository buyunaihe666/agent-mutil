"""Conversation Service - session lifecycle, message storage, context window, export."""

import asyncio
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# --- Schemas ---

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ExportFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"
    PDF = "pdf"


class ConversationCreate(BaseModel):
    first_message: str = Field(..., min_length=1)
    user_id: Optional[str] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[ConversationStatus] = None
    is_pinned: Optional[bool] = None
    pinned_space: Optional[str] = None


class ConversationSummary(BaseModel):
    id: str
    title: Optional[str] = None
    status: str
    is_pinned: bool = False
    pinned_space: Optional[str] = None
    message_count: int = 0
    updated_at: str


class ConversationDetail(BaseModel):
    id: str
    title: Optional[str] = None
    status: str
    user_id: Optional[str] = None
    context_window_size: int = 50
    is_pinned: bool = False
    pinned_space: Optional[str] = None
    created_at: str
    updated_at: str


class MessageCreate(BaseModel):
    role: str
    content: Optional[str] = None
    agent_id: Optional[str] = None
    content_blocks: Optional[dict] = None
    parent_message_id: Optional[str] = None


class MessageEdit(BaseModel):
    content: str


class MessageDetail(BaseModel):
    id: str
    conversation_id: str
    role: str
    agent_id: Optional[str] = None
    content: Optional[str] = None
    content_blocks: Optional[dict] = None
    token_count: Optional[int] = None
    parent_message_id: Optional[str] = None
    is_edited: bool = False
    edited_at: Optional[str] = None
    created_at: str


class MessagePage(BaseModel):
    messages: list[MessageDetail]
    next_cursor: Optional[str] = None
    has_more: bool = False


class ExportRequest(BaseModel):
    format: ExportFormat = ExportFormat.MARKDOWN


# --- In-Memory Store (mock for testing) ---

class ConversationStore:
    """In-memory conversation store. Will be replaced with DB-backed Repository."""

    def __init__(self):
        self.conversations: dict[str, dict] = {}
        self.messages: dict[str, list[dict]] = {}  # conv_id -> [messages]
        self._redis_buffer: dict[str, list[dict]] = {}  # conv_id -> buffered messages
        self._flush_lock = asyncio.Lock()

    # --- Conversation CRUD ---

    async def list_conversations(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        pinned_space: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        results = list(self.conversations.values())

        if user_id:
            results = [c for c in results if c.get("user_id") == user_id]
        if status:
            results = [c for c in results if c["status"] == status]
        if search:
            results = [c for c in results if search.lower() in (c.get("title") or "").lower()]
        if pinned_space:
            results = [c for c in results if c.get("pinned_space") == pinned_space]

        # Sort: pinned first, then by updated_at DESC
        results.sort(key=lambda c: (not c.get("is_pinned", False), c.get("updated_at", "")), reverse=False)
        results.sort(key=lambda c: c.get("is_pinned", False), reverse=True)

        total = len(results)
        page = results[offset : offset + limit]
        return page, total

    async def create_conversation(self, first_message: str, user_id: Optional[str] = None) -> dict:
        conv_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conv = {
            "id": conv_id,
            "title": None,
            "status": "active",
            "user_id": user_id,
            "context_window_size": 50,
            "is_pinned": False,
            "pinned_space": None,
            "message_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        self.conversations[conv_id] = conv
        self.messages[conv_id] = []

        # Auto-generate title placeholder
        conv["title"] = first_message[:20] + ("..." if len(first_message) > 20 else "")

        return conv

    async def get_conversation(self, conv_id: str) -> Optional[dict]:
        return self.conversations.get(conv_id)

    async def update_conversation(self, conv_id: str, data: ConversationUpdate) -> Optional[dict]:
        conv = self.conversations.get(conv_id)
        if not conv:
            return None
        if data.title is not None:
            conv["title"] = data.title
        if data.status is not None:
            conv["status"] = data.status.value if isinstance(data.status, ConversationStatus) else data.status
        if data.is_pinned is not None:
            conv["is_pinned"] = data.is_pinned
        if data.pinned_space is not None:
            conv["pinned_space"] = data.pinned_space
        conv["updated_at"] = datetime.now(timezone.utc).isoformat()
        return conv

    async def delete_conversation(self, conv_id: str) -> bool:
        if conv_id in self.conversations:
            del self.conversations[conv_id]
            self.messages.pop(conv_id, None)
            self._redis_buffer.pop(conv_id, None)
            return True
        return False

    # --- Message Management ---

    async def add_message(self, conv_id: str, msg: MessageCreate) -> Optional[dict]:
        if conv_id not in self.conversations:
            return None
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        msg_record = {
            "id": msg_id,
            "conversation_id": conv_id,
            "role": msg.role,
            "agent_id": msg.agent_id,
            "content": msg.content,
            "content_blocks": msg.content_blocks,
            "token_count": None,
            "parent_message_id": msg.parent_message_id,
            "is_edited": False,
            "edited_at": None,
            "created_at": now,
        }
        self.messages.setdefault(conv_id, []).append(msg_record)
        self.conversations[conv_id]["message_count"] += 1
        self.conversations[conv_id]["updated_at"] = now
        return msg_record

    async def get_messages(
        self, conv_id: str, cursor: Optional[str] = None, limit: int = 50
    ) -> MessagePage:
        msgs = self.messages.get(conv_id, [])
        msgs_sorted = sorted(msgs, key=lambda m: m["created_at"])
        start_idx = 0
        if cursor:
            for i, m in enumerate(msgs_sorted):
                if m["id"] == cursor:
                    start_idx = i + 1
                    break

        page = msgs_sorted[start_idx : start_idx + limit]
        has_more = (start_idx + limit) < len(msgs_sorted)
        next_cursor = page[-1]["id"] if page and has_more else None

        return MessagePage(
            messages=[MessageDetail(**m) for m in page],
            next_cursor=next_cursor,
            has_more=has_more,
        )

    async def edit_message(self, conv_id: str, msg_id: str, new_content: str) -> Optional[dict]:
        msgs = self.messages.get(conv_id, [])
        for m in msgs:
            if m["id"] == msg_id:
                m["content"] = new_content
                m["is_edited"] = True
                m["edited_at"] = datetime.now(timezone.utc).isoformat()
                return m
        return None

    # --- Context Window ---

    async def build_context(self, conv_id: str, agent_id: Optional[str] = None, max_tokens: int = 8000) -> list[dict]:
        """Build context window using sliding window strategy."""
        msgs = self.messages.get(conv_id, [])
        msgs_sorted = sorted(msgs, key=lambda m: m["created_at"])

        # Agent isolation: supervisor sees all, workers see only their subtask
        if agent_id and agent_id != "orchestrator":
            msgs_sorted = [m for m in msgs_sorted if m.get("agent_id") in (agent_id, None)]

        # Sliding window: keep last N messages
        window_size = self.conversations.get(conv_id, {}).get("context_window_size", 50)
        recent = msgs_sorted[-window_size:]

        return recent

    # --- Export ---

    async def export_conversation(self, conv_id: str, fmt: ExportFormat) -> str:
        msgs = self.messages.get(conv_id, [])
        msgs_sorted = sorted(msgs, key=lambda m: m["created_at"])
        conv = self.conversations.get(conv_id, {})

        if fmt == ExportFormat.MARKDOWN:
            return self._export_markdown(conv, msgs_sorted)
        elif fmt == ExportFormat.JSON:
            return self._export_json(conv, msgs_sorted)
        else:
            return f"PDF export for conversation {conv_id} (placeholder)"

    def _export_markdown(self, conv: dict, msgs: list) -> str:
        lines = [f"# {conv.get('title', 'Untitled Conversation')}", "", f"*Exported: {datetime.now(timezone.utc).isoformat()}*", ""]
        for m in msgs:
            role_label = m["role"].upper()
            agent_id = m.get("agent_id", "")
            if agent_id:
                role_label += f" (Agent: {agent_id[:8]})"
            lines.append(f"### {role_label}")
            lines.append("")
            if m.get("content"):
                lines.append(m["content"])
            lines.append("")
        return "\n".join(lines)

    def _export_json(self, conv: dict, msgs: list) -> str:
        import json
        return json.dumps({"conversation": conv, "messages": msgs}, indent=2, ensure_ascii=False)

    # --- Redis Buffer (simulated) ---

    async def buffer_message(self, conv_id: str, msg: dict) -> None:
        """Buffer message in simulated Redis list before batch write."""
        self._redis_buffer.setdefault(conv_id, []).append(msg)
        if len(self._redis_buffer[conv_id]) >= 10:
            await self._flush_buffer(conv_id)

    async def _flush_buffer(self, conv_id: str) -> None:
        """Flush buffered messages to persistent store."""
        async with self._flush_lock:
            buffered = self._redis_buffer.pop(conv_id, [])
            for msg in buffered:
                self.messages.setdefault(conv_id, []).append(msg)
            logger.info("Buffer flushed", conversation_id=conv_id, count=len(buffered))

    async def flush_all(self) -> None:
        """Force flush all buffers."""
        for conv_id in list(self._redis_buffer.keys()):
            await self._flush_buffer(conv_id)

    async def regenerate_response(self, conv_id: str, msg_id: str) -> Optional[dict]:
        """Regenerate an agent response after a message edit."""
        msgs = self.messages.get(conv_id, [])
        for m in msgs:
            if m["id"] == msg_id:
                # Create a new response as child of the edited message
                new_msg = await self.add_message(
                    conv_id,
                    MessageCreate(
                        role="assistant",
                        content=f"Regenerated response for message {msg_id}",
                        parent_message_id=msg_id,
                    ),
                )
                return new_msg
        return None


# Global store instance
conversation_store = ConversationStore()
