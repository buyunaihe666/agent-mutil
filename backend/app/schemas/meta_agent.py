"""Meta-Agent Pydantic schemas for triage results and layer events."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class TriageResult(BaseModel):
    """决策Agent 复杂度判断结果"""
    complexity: Literal["simple", "complex"] = Field(
        ..., description="任务复杂度：simple=单Agent可完成, complex=需多Agent协作"
    )
    reasoning: str = Field(..., description="判断理由")
    suggested_direction: Optional[str] = Field(None, description="建议的处理方向")
    suggested_agent_name: Optional[str] = Field(None, description="simple时：建议委派的Agent名称")
    needs_plan: bool = Field(False, description="complex时：是否需要生成Plan")


class MetaAgentEvent(BaseModel):
    """Meta-Agent 层级事件"""
    layer: Literal["decision", "strategy", "execution", "strategy_review"] = Field(
        ..., description="当前层级"
    )
    agent_name: str = Field(..., description="Meta-Agent 名称")
    status: Literal["started", "completed", "error"] = Field(...)
    data: Optional[dict] = Field(None, description="附加数据（TriageResult / Plan / Results）")


class LayerTransition(BaseModel):
    """层级切换事件"""
    from_layer: str = Field(..., description="来源层级")
    to_layer: str = Field(..., description="目标层级")
    reason: Optional[str] = Field(None, description="切换原因")
