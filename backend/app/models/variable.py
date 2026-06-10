"""VariableTable model - cross-step key-value storage."""

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class VariableTable(BaseModel):
    __tablename__ = "variable_table"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    data_type: Mapped[str] = mapped_column(String(50), default="string")
