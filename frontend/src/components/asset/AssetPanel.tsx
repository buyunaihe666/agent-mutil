/** Asset Panel UI - file browsing, search, preview, upload, download. */

import { type AssetItem, addAsset, removeAsset, setSearchQuery, setSelectedAsset } from "@/features/asset/assetSlice";
import { t } from "@/i18n";
import { EmptyState } from "@/components/shared/EmptyState";
import type { AppDispatch, RootState } from "@/store";
import { useRef } from "react";
import { useDispatch, useSelector } from "react-redux";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getAssetIcon(previewType: string): string {
  switch (previewType) {
    case "image":
      return "🖼️";
    case "pdf":
      return "📕";
    case "table":
      return "📊";
    case "text":
      return "📄";
    default:
      return "📎";
  }
}

function getPreviewType(file: File): string {
  if (file.type.startsWith("image/")) return "image";
  if (file.type === "application/pdf") return "pdf";
  if (file.type.includes("csv") || file.type.includes("spreadsheet") || file.type.includes("excel")) return "table";
  if (file.type.startsWith("text/") || file.type === "application/json") return "text";
  return "other";
}

let assetIdCounter = 0;
function createAssetId(): string {
  assetIdCounter += 1;
  return `asset-${Date.now()}-${assetIdCounter}`;
}

type AssetPanelProps = {
  variant?: "full" | "compact";
};

const MOCK_ASSETS: AssetItem[] = [
  {
    id: "m1",
    filename: "sales_report.csv",
    original_filename: "sales_report.csv",
    file_size: 1024,
    mime_type: "text/csv",
    preview_type: "table",
    created_at: new Date().toISOString(),
  },
  {
    id: "m2",
    filename: "architecture.png",
    original_filename: "architecture.png",
    file_size: 1024 * 1024,
    mime_type: "image/png",
    preview_type: "image",
    created_at: new Date().toISOString(),
  },
  {
    id: "m3",
    filename: "readme.md",
    original_filename: "readme.md",
    file_size: 512,
    mime_type: "text/markdown",
    preview_type: "text",
    created_at: new Date().toISOString(),
  },
];

export function AssetPanel({ variant = "full" }: AssetPanelProps) {
  const dispatch = useDispatch<AppDispatch>();
  const {
    assets: assetsFromStore,
    selectedAssetId,
    searchQuery,
  } = useSelector((state: RootState) => state.asset);

  const fileInputRef = useRef<HTMLInputElement>(null);
  // Cache uploaded File objects for download
  const fileCache = useRef<Map<string, File>>(new Map());

  const isUsingFallbackAssets = assetsFromStore.length === 0;
  const assets = isUsingFallbackAssets ? MOCK_ASSETS : assetsFromStore;

  const filtered = assets.filter(
    (a) => !searchQuery || a.original_filename.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const selected = assets.find((a) => a.id === selectedAssetId);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const newAsset: AssetItem = {
      id: createAssetId(),
      filename: file.name,
      original_filename: file.name,
      file_size: file.size,
      mime_type: file.type || undefined,
      preview_type: getPreviewType(file),
      created_at: new Date().toISOString(),
    };
    dispatch(addAsset(newAsset));
    fileCache.current.set(newAsset.id, file);
    e.target.value = "";
  };

  const handleDownload = () => {
    if (!selected) return;
    const file = fileCache.current.get(selected.id);
    if (file) {
      const url = URL.createObjectURL(file);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.name;
      a.click();
      URL.revokeObjectURL(url);
    } else {
      // For assets without cached file data (e.g., from mock), show placeholder message
      window.alert("此文件不在本地缓存中，无法下载");
    }
  };

  const handleDelete = () => {
    if (!selected) return;
    dispatch(removeAsset(selected.id));
    fileCache.current.delete(selected.id);
  };

  const isCompact = variant === "compact";
  const styles = isCompact
    ? {
        root: "h-full flex flex-col bg-white text-slate-900",
        header: "p-3 border-b border-slate-200",
        input:
          "w-full mt-2 px-2 py-1 text-xs rounded bg-slate-50 text-slate-900 placeholder-slate-400 border border-slate-200 outline-none focus:border-blue-400",
        item: "hover:bg-slate-100",
        itemSelected: "bg-blue-50 text-blue-700",
        size: "text-slate-400",
        empty: "text-center text-slate-400 text-xs py-8",
        previewPanel: "border-t border-slate-200 p-3",
        previewCard: "bg-slate-50 rounded p-2 text-xs space-y-1 border border-slate-200",
        previewIcon:
          "mt-2 h-24 bg-white rounded flex items-center justify-center text-2xl border border-slate-200",
        downloadButton: "flex-1 py-1 text-xs rounded bg-blue-600 text-white hover:bg-blue-700",
        deleteButton: "flex-1 py-1 text-xs rounded bg-red-100 text-red-700 hover:bg-red-200",
        uploadButton: "px-2 py-1 text-xs rounded bg-blue-600 text-white hover:bg-blue-700",
      }
    : {
        root: "h-full flex flex-col bg-sidebar text-white",
        header: "p-3 border-b border-sidebar-hover",
        input:
          "w-full mt-2 px-2 py-1 text-xs rounded bg-sidebar-active text-white placeholder-white/40 border-0 outline-none",
        item: "hover:bg-sidebar-hover",
        itemSelected: "bg-sidebar-active",
        size: "text-white/40",
        empty: "text-center text-white/40 text-xs py-8",
        previewPanel: "border-t border-sidebar-hover p-3",
        previewCard: "bg-sidebar-active rounded p-2 text-xs space-y-1",
        previewIcon: "mt-2 h-24 bg-sidebar rounded flex items-center justify-center text-2xl",
        downloadButton: "flex-1 py-1 text-xs rounded bg-blue-600 hover:bg-blue-700",
        deleteButton: "flex-1 py-1 text-xs rounded bg-red-600/50 hover:bg-red-600",
        uploadButton: "px-2 py-1 text-xs rounded bg-blue-600 hover:bg-blue-700",
      };

  return (
    <div className={styles.root}>
      {/* Header */}
      <div className={styles.header}>
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium">{t("nav.assets")}</h2>
          <button
            type="button"
            className={styles.uploadButton}
            title="上传文件"
            onClick={() => fileInputRef.current?.click()}
          >
            + 上传
          </button>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={handleFileChange}
          />
        </div>
        <input
          value={searchQuery}
          aria-label={t("common.search")}
          onChange={(e) => dispatch(setSearchQuery(e.target.value))}
          placeholder={t("common.search")}
          className={styles.input}
        />
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {filtered.length === 0 ? (
          <EmptyState
            icon="📂"
            title={t("status.empty")}
            description="点击「上传」按钮添加文件"
          />
        ) : (
          filtered.map((asset) => (
            <button
              key={asset.id}
              type="button"
              aria-pressed={asset.id === selectedAssetId}
              onClick={() =>
                dispatch(setSelectedAsset(asset.id === selectedAssetId ? null : asset.id))
              }
              className={`w-full text-left px-2 py-1.5 rounded text-xs flex items-center gap-2 transition-colors ${
                asset.id === selectedAssetId ? styles.itemSelected : styles.item
              }`}
            >
              <span>{getAssetIcon(asset.preview_type)}</span>
              <span className="truncate flex-1">{asset.original_filename}</span>
              <span className={styles.size}>{formatSize(asset.file_size)}</span>
            </button>
          ))
        )}
      </div>

      {/* Preview Panel */}
      {selected && (
        <div className={styles.previewPanel}>
          <h3 className="text-xs font-medium mb-2 truncate">{selected.original_filename}</h3>
          <div className={styles.previewCard}>
            <div>
              {t("asset.type")}: {selected.preview_type}
            </div>
            <div>
              {t("asset.size")}: {formatSize(selected.file_size)}
            </div>
            <div>
              {t("asset.mime")}: {selected.mime_type ?? "unknown"}
            </div>
            <div className={styles.previewIcon}>{getAssetIcon(selected.preview_type)}</div>
          </div>
          <div className="flex gap-1 mt-2">
            <button
              className={styles.downloadButton}
              title={t("action.download")}
              type="button"
              onClick={handleDownload}
            >
              ⬇ {t("action.download")}
            </button>
            <button
              className={styles.deleteButton}
              title={t("action.delete")}
              type="button"
              onClick={handleDelete}
            >
              🗑️
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
