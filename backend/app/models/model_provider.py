"""ModelProvider model - LLM provider configuration."""

from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ModelProvider(BaseModel):
    __tablename__ = "model_providers"

    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    api_base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    models_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    rate_limit_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
