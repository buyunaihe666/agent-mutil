"""System Monitoring - hardware stats, container monitoring, WebSocket push."""

import asyncio
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# --- Enums ---

class AgentActivityStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    BLOCKED = "blocked"
    ERROR = "error"


# --- Schemas ---

class HardwareStats(BaseModel):
    """System hardware resource statistics."""
    cpu_percent: float = 0.0
    memory_total_mb: float = 0.0
    memory_used_mb: float = 0.0
    memory_percent: float = 0.0
    disk_total_gb: float = 0.0
    disk_used_gb: float = 0.0
    disk_percent: float = 0.0
    gpu_name: Optional[str] = None
    gpu_memory_total_mb: Optional[float] = None
    gpu_memory_used_mb: Optional[float] = None
    gpu_utilization_percent: Optional[float] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ContainerStats(BaseModel):
    """Docker container resource statistics."""
    container_id: str
    container_name: str
    cpu_percent: float = 0.0
    memory_usage_mb: float = 0.0
    memory_limit_mb: float = 0.0
    memory_percent: float = 0.0
    network_rx_mb: float = 0.0
    network_tx_mb: float = 0.0
    status: str = "running"
    uptime_seconds: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentActivity(BaseModel):
    """Agent activity status update."""
    agent_id: str
    agent_name: str
    agent_emoji: Optional[str] = None
    status: AgentActivityStatus = AgentActivityStatus.IDLE
    message: Optional[str] = None
    conversation_id: Optional[str] = None
    started_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SystemStats(BaseModel):
    """Combined system statistics."""
    hardware: HardwareStats
    containers: list[ContainerStats] = Field(default_factory=list)
    agent_activities: list[AgentActivity] = Field(default_factory=list)
    active_conversations: int = 0
    active_ws_connections: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# --- Monitoring Service ---

class MonitorService:
    """Monitors system resources, containers, and agent activities."""

    def __init__(self):
        self._agent_activities: dict[str, AgentActivity] = {}  # agent_id -> activity
        self._container_stats: dict[str, ContainerStats] = {}
        self._collection_task: Optional[asyncio.Task] = None
        self._is_collecting = False

    async def start_collection(self, interval: int = 5) -> None:
        """Start periodic stats collection."""
        if self._is_collecting:
            return
        self._is_collecting = True
        self._collection_task = asyncio.create_task(self._collect_loop(interval))
        logger.info("Monitoring collection started", interval=interval)

    async def stop_collection(self) -> None:
        """Stop periodic stats collection."""
        self._is_collecting = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoring collection stopped")

    async def _collect_loop(self, interval: int) -> None:
        """Periodic collection loop."""
        while self._is_collecting:
            try:
                stats = await self.collect_hardware_stats()
                logger.debug("Hardware stats collected", cpu=stats.cpu_percent)
            except Exception as e:
                logger.error("Stats collection failed", error=str(e))
            await asyncio.sleep(interval)

    async def collect_hardware_stats(self) -> HardwareStats:
        """Collect hardware resource statistics.

        Note: Mock implementation for testing. Real implementation uses psutil + pynvml.
        """
        # Mock stats
        return HardwareStats(
            cpu_percent=25.5,
            memory_total_mb=32768,
            memory_used_mb=16384,
            memory_percent=50.0,
            disk_total_gb=500.0,
            disk_used_gb=250.0,
            disk_percent=50.0,
            gpu_name="NVIDIA RTX 4090",
            gpu_memory_total_mb=24576,
            gpu_memory_used_mb=8192,
            gpu_utilization_percent=35.0,
        )

    async def collect_container_stats(self) -> list[ContainerStats]:
        """Collect Docker container statistics.

        Note: Mock implementation for testing. Real implementation uses docker-py.
        """
        # Mock container stats
        mock_containers = [
            ("nexus-postgres", "postgres"),
            ("nexus-redis", "redis"),
            ("nexus-backend", "backend"),
            ("nexus-frontend", "frontend"),
            ("nexus-nginx", "nginx"),
        ]
        stats = []
        for i, (name, _) in enumerate(mock_containers):
            stats.append(ContainerStats(
                container_id=f"mock-{uuid.uuid4().hex[:12]}",
                container_name=name,
                cpu_percent=5.0 + i * 3,
                memory_usage_mb=128 + i * 64,
                memory_limit_mb=1024,
                memory_percent=(128 + i * 64) / 1024 * 100,
                network_rx_mb=10.0 + i,
                network_tx_mb=5.0 + i,
                status="running",
                uptime_seconds=3600 * (i + 1),
            ))
        self._container_stats = {s.container_name: s for s in stats}
        return stats

    async def update_agent_activity(self, activity: AgentActivity) -> None:
        """Update or create an agent activity status."""
        self._agent_activities[activity.agent_id] = activity
        logger.info("Agent activity updated", agent_id=activity.agent_id, status=activity.status)

    async def get_agent_activities(self) -> list[AgentActivity]:
        """Get all current agent activities."""
        return list(self._agent_activities.values())

    async def get_system_stats(self) -> SystemStats:
        """Get complete system statistics."""
        hardware = await self.collect_hardware_stats()
        containers = await self.collect_container_stats()
        activities = await self.get_agent_activities()

        return SystemStats(
            hardware=hardware,
            containers=containers,
            agent_activities=activities,
            active_conversations=0,
            active_ws_connections=0,
        )

    async def push_stats_via_ws(self, ws_manager) -> None:
        """Push current stats to all connected monitor WebSocket clients."""
        stats = await self.get_system_stats()
        # ws_manager is injected to avoid circular import
        from app.core.ws import MessageType, ServerMessage
        msg = ServerMessage(
            type=MessageType.HARDWARE_STATS,
            data=stats.model_dump(),
        )
        await ws_manager.broadcast_monitor(msg)


# Global service
monitor_service = MonitorService()
