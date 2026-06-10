"""AgentVersion model - configuration version history."""

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class AgentVersion(BaseModel):
    __tablename__ = "agent_versions"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tools_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    config_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    change_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    agent: Mapped["Agent"] = relationship("Agent", backref="versions")
