"""Agent REST API endpoints for NEXUS AI."""

import structlog
from fastapi import APIRouter, HTTPException

from app.core.agent_service import AgentDetail, AgentSummary, agent_store

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/agents", response_model=list[AgentSummary])
async def list_agents(search: str = "", permission_level: int | None = None):
    """List all agents with optional filtering."""
    results, _total = await agent_store.list_agents(
        search=search,
        permission_level=permission_level,
    )
    return results


@router.get("/agents/{agent_id}", response_model=AgentDetail)
async def get_agent(agent_id: str):
    """Get a single agent by ID, including system_prompt and full config."""
    agent = await agent_store.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/agents/templates", response_model=list[dict])
async def list_templates():
    """List all agent templates."""
    return agent_store.get_templates()
