"""Agent model."""

import uuid
from typing import Optional

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Agent(BaseModel):
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tools_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    default_model: Mapped[str] = mapped_column(String(100), default="deepseek-chat")
    permission_level: Mapped[int] = mapped_column(Integer, default=1)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300)
    is_preset: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_meta: Mapped[bool] = mapped_column(Boolean, default=False)
    config_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
