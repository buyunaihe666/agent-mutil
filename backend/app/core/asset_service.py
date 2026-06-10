"""Asset Service - file upload, storage abstraction, preview generation."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# --- Enums ---

class StorageBackend(str, Enum):
    LOCAL = "local"
    S3 = "s3"


class AssetType(str, Enum):
    FILE = "file"
    KNOWLEDGE = "knowledge"


class PreviewType(str, Enum):
    IMAGE = "image"
    PDF = "pdf"
    TEXT = "text"
    TABLE = "table"
    NONE = "none"


# --- Schemas ---

class AssetCreate(BaseModel):
    filename: str
    original_filename: str
    file_path: str
    file_size: int = 0
    mime_type: Optional[str] = None
    asset_type: AssetType = AssetType.FILE
    storage_backend: StorageBackend = StorageBackend.LOCAL
    uploaded_by: Optional[str] = None


class AssetUpdate(BaseModel):
    filename: Optional[str] = None
    metadata: Optional[dict] = None


class AssetSummary(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int = 0
    mime_type: Optional[str] = None
    asset_type: str
    preview_type: str
    uploaded_by: Optional[str] = None
    created_at: str
    updated_at: str


class AssetDetail(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int = 0
    mime_type: Optional[str] = None
    asset_type: str
    storage_backend: str
    preview_type: str
    metadata: Optional[dict] = None
    uploaded_by: Optional[str] = None
    created_at: str
    updated_at: str


# --- Helpers ---

def _get_preview_type(mime_type: Optional[str]) -> str:
    """Determine preview type from MIME type."""
    if not mime_type:
        return PreviewType.NONE
    if mime_type.startswith("image/"):
        return PreviewType.IMAGE
    if mime_type == "application/pdf":
        return PreviewType.PDF
    if mime_type == "text/csv" or mime_type in ("application/vnd.ms-excel",
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
        return PreviewType.TABLE
    if mime_type.startswith("text/") or mime_type in ("application/json", "application/javascript"):
        return PreviewType.TEXT
    return PreviewType.NONE


def _human_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# --- Asset Store ---

class AssetStore:
    """In-memory asset store with storage abstraction layer."""

    def __init__(self, storage_backend: StorageBackend = StorageBackend.LOCAL):
        self.assets: dict[str, dict] = {}
        self.storage_backend = storage_backend
        self._storage_path = Path("assets")
        self._init_storage()

    def _init_storage(self):
        """Ensure storage path exists for local backend."""
        if self.storage_backend == StorageBackend.LOCAL:
            self._storage_path.mkdir(parents=True, exist_ok=True)

    async def list_assets(
        self,
        search: Optional[str] = None,
        asset_type: Optional[str] = None,
        mime_type_prefix: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        results = list(self.assets.values())

        if search:
            results = [a for a in results if
                       search.lower() in a["filename"].lower() or
                       search.lower() in a["original_filename"].lower()]
        if asset_type:
            results = [a for a in results if a["asset_type"] == asset_type]
        if mime_type_prefix:
            results = [a for a in results if (a.get("mime_type") or "").startswith(mime_type_prefix)]
        if uploaded_by:
            results = [a for a in results if a.get("uploaded_by") == uploaded_by]

        results.sort(key=lambda a: a["created_at"], reverse=True)
        total = len(results)
        return results[offset : offset + limit], total

    async def create_asset(self, data: AssetCreate) -> dict:
        asset_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        asset = {
            "id": asset_id,
            "filename": data.filename,
            "original_filename": data.original_filename,
            "file_path": data.file_path,
            "file_size": data.file_size,
            "mime_type": data.mime_type,
            "asset_type": data.asset_type.value if isinstance(data.asset_type, AssetType) else data.asset_type,
            "storage_backend": data.storage_backend.value if isinstance(data.storage_backend, StorageBackend) else data.storage_backend,
            "preview_type": _get_preview_type(data.mime_type),
            "metadata": {},
            "uploaded_by": data.uploaded_by,
            "created_at": now,
            "updated_at": now,
        }
        self.assets[asset_id] = asset
        logger.info("Asset created", asset_id=asset_id, filename=data.original_filename)
        return asset

    async def get_asset(self, asset_id: str) -> Optional[dict]:
        return self.assets.get(asset_id)

    async def update_asset(self, asset_id: str, data: AssetUpdate) -> Optional[dict]:
        asset = self.assets.get(asset_id)
        if not asset:
            return None
        if data.filename is not None:
            asset["filename"] = data.filename
        if data.metadata is not None:
            asset["metadata"] = data.metadata
        asset["updated_at"] = datetime.now(timezone.utc).isoformat()
        return asset

    async def delete_asset(self, asset_id: str) -> bool:
        if asset_id in self.assets:
            del self.assets[asset_id]
            return True
        return False

    async def get_preview(self, asset_id: str) -> Optional[dict]:
        """Get preview data for an asset."""
        asset = self.assets.get(asset_id)
        if not asset:
            return None
        preview_type = asset["preview_type"]
        preview_data = {
            "asset_id": asset_id,
            "preview_type": preview_type,
            "filename": asset["original_filename"],
            "mime_type": asset["mime_type"],
            "file_size": _human_size(asset["file_size"]),
        }

        if preview_type == PreviewType.IMAGE:
            preview_data["thumbnail_url"] = f"/api/assets/{asset_id}/thumbnail"
        elif preview_type == PreviewType.TEXT:
            preview_data["content_preview"] = f"Text content placeholder for {asset['original_filename']}"
        elif preview_type == PreviewType.TABLE:
            preview_data["columns"] = ["Column1", "Column2"]
            preview_data["rows"] = []
        elif preview_type == PreviewType.PDF:
            preview_data["pdf_url"] = f"/api/assets/{asset_id}/pdf"

        return preview_data

    def get_storage_info(self) -> dict:
        """Get storage backend info."""
        total_size = sum(a["file_size"] for a in self.assets.values())
        return {
            "backend": self.storage_backend.value if isinstance(self.storage_backend, StorageBackend) else self.storage_backend,
            "total_files": len(self.assets),
            "total_size_bytes": total_size,
            "total_size_human": _human_size(total_size),
        }


# Global store
asset_store = AssetStore()
