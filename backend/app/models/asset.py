"""Asset model - uploaded files and knowledge base documents."""

from typing import Optional

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Asset(BaseModel):
    __tablename__ = "assets"

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    mime_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(50), default="file")
    storage_backend: Mapped[str] = mapped_column(String(50), default="local")
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
