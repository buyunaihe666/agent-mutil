/** Export dialog — choose format and download conversation/agent/data. */

import { Modal } from "@/components/shared/Modal";
import { t } from "@/i18n";
import { useState } from "react";

type ExportFormat = "markdown" | "json" | "pdf";

interface ExportDialogProps {
  open: boolean;
  onClose: () => void;
  onExport: (format: ExportFormat, options: ExportOptions) => void;
}

interface ExportOptions {
  includeMessages: boolean;
  includeAgentInfo: boolean;
  includeTimestamps: boolean;
}

const FORMAT_LABELS: Record<ExportFormat, { label: string; ext: string; icon: string }> = {
  markdown: { label: "Markdown", ext: ".md", icon: "📝" },
  json: { label: "JSON", ext: ".json", icon: "📋" },
  pdf: { label: "PDF", ext: ".pdf", icon: "📕" },
};

export function ExportDialog({ open, onClose, onExport }: ExportDialogProps) {
  const [format, setFormat] = useState<ExportFormat>("markdown");
  const [options, setOptions] = useState<ExportOptions>({
    includeMessages: true,
    includeAgentInfo: true,
    includeTimestamps: true,
  });

  const handleExport = () => {
    onExport(format, options);
    onClose();
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={t("action.export")}
      footer={
        <>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-lg border hover:bg-accent"
          >
            {t("action.cancel")}
          </button>
          <button
            type="button"
            onClick={handleExport}
            className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700"
          >
            {t("action.export")}
          </button>
        </>
      }
    >
      <div className="space-y-4">
        {/* Format Selection */}
        <div>
          <div className="text-sm font-medium mb-2 block">{t("action.export")} Format</div>
          <div className="grid grid-cols-3 gap-2">
            {(Object.entries(FORMAT_LABELS) as [ExportFormat, typeof FORMAT_LABELS.markdown][]).map(
              ([key, info]) => (
                <button
                  type="button"
                  key={key}
                  onClick={() => setFormat(key)}
                  className={`flex flex-col items-center gap-1 p-3 rounded-lg border text-sm transition-colors ${
                    format === key
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-950"
                      : "hover:bg-accent"
                  }`}
                >
                  <span className="text-xl">{info.icon}</span>
                  <span className="font-medium">{info.label}</span>
                  <span className="text-xs text-muted-foreground">{info.ext}</span>
                </button>
              ),
            )}
          </div>
        </div>

        {/* Options */}
        <div>
          <div className="text-sm font-medium mb-2 block">Include</div>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={options.includeMessages}
                onChange={(e) => setOptions({ ...options, includeMessages: e.target.checked })}
                className="rounded"
              />
              Messages
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={options.includeAgentInfo}
                onChange={(e) => setOptions({ ...options, includeAgentInfo: e.target.checked })}
                className="rounded"
              />
              Agent Information
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={options.includeTimestamps}
                onChange={(e) => setOptions({ ...options, includeTimestamps: e.target.checked })}
                className="rounded"
              />
              Timestamps
            </label>
          </div>
        </div>
      </div>
    </Modal>
  );
}
