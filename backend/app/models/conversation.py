"""Conversation model."""

from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Conversation(BaseModel):
    __tablename__ = "conversations"

    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Reserved for JWT auth"
    )
    status: Mapped[str] = mapped_column(String(50), default="active")
    context_window_size: Mapped[int] = mapped_column(Integer, default=50)
