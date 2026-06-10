"""Security Service - permissions, audit logging, data desensitization, rate limiting."""

import re
from datetime import datetime, timezone
from enum import IntEnum
from typing import Optional

import structlog

from app.core.yaml_config import get_yaml_config

logger = structlog.get_logger(__name__)

yaml_config = get_yaml_config()


# --- Permission Levels ---

class PermissionLevel(IntEnum):
    READ_ONLY = 1   # L1: Read-only access
    ANALYZE = 2     # L2: Analysis, queries
    OPERATE = 3     # L3: Code execution, file operations
    ADMIN = 4       # L4: Full management


# --- Audit Log ---

class AuditLogger:
    """Append-only audit log (INSERT + SELECT only, no UPDATE/DELETE per design)."""

    def __init__(self):
        self._logs: list[dict] = []  # In-memory for testing; DB-backed in production

    def log(
        self,
        action_type: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        detail: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> dict:
        entry = {
            "action_type": action_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "agent_id": agent_id,
            "detail_json": detail or {},
            "ip_address": ip_address,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._logs.append(entry)
        logger.info("Audit log entry created", action_type=action_type, resource_type=resource_type)
        return entry

    def query(
        self,
        action_type: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        results = self._logs
        if action_type:
            results = [l for l in results if l["action_type"] == action_type]
        if user_id:
            results = [l for l in results if l["user_id"] == user_id]
        if agent_id:
            results = [l for l in results if l["agent_id"] == agent_id]
        return results[-limit:]

    def clear(self) -> None:
        self._logs.clear()


# Global audit logger
audit_logger = AuditLogger()


# --- Data Desensitization ---

def desensitize(text: str) -> str:
    """Apply desensitization rules to text before sending to client."""
    rules = yaml_config.get("security", {}).get("desensitize_rules", [])
    result = text
    for rule in rules:
        try:
            result = re.sub(rule["pattern"], rule["replacement"], result)
        except re.error:
            logger.warning("Invalid desensitize regex pattern", pattern=rule.get("pattern", ""))
    return result


# --- Rate Limiter ---

class RateLimiter:
    """Simple in-memory sliding window rate limiter."""

    def __init__(self):
        self._windows: dict[str, list[float]] = {}

    def check(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        """Check if request is allowed. Returns True if allowed."""
        import time
        now = time.time()
        if key not in self._windows:
            self._windows[key] = []
        # Remove expired entries
        self._windows[key] = [t for t in self._windows[key] if now - t < window_seconds]
        if len(self._windows[key]) >= max_requests:
            return False
        self._windows[key].append(now)
        return True

    def remaining(self, key: str, max_requests: int, window_seconds: int = 60) -> int:
        import time
        now = time.time()
        if key not in self._windows:
            return max_requests
        self._windows[key] = [t for t in self._windows[key] if now - t < window_seconds]
        return max(0, max_requests - len(self._windows[key]))

    def clear(self) -> None:
        self._windows.clear()


# Global rate limiters
default_limiter = RateLimiter()
llm_limiter = RateLimiter()
