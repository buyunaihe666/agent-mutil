/** Model selector dropdown component. */

import { t } from "@/i18n";
import { useState } from "react";

export interface ModelOption {
  id: string;
  name: string;
  provider: string;
}

interface ModelSelectorProps {
  models: ModelOption[];
  selectedModel: string;
  onSelect: (modelId: string) => void;
}

export function ModelSelector({ models, selectedModel, onSelect }: ModelSelectorProps) {
  const [open, setOpen] = useState(false);

  const selected = models.find((m) => m.id === selectedModel);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 px-2 py-1 text-xs rounded border hover:bg-accent"
        title={t("model.select")}
      >
        <span>{selected?.name ?? t("model.default")}</span>
        <span className="text-muted-foreground">▼</span>
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setOpen(false)}
            onKeyDown={(e) => {
              if (e.key === "Escape") setOpen(false);
            }}
          />
          <div className="absolute top-full mt-1 right-0 z-20 w-56 bg-popover border rounded-lg shadow-lg py-1 max-h-64 overflow-y-auto">
            {models.map((model) => (
              <button
                type="button"
                key={model.id}
                onClick={() => {
                  onSelect(model.id);
                  setOpen(false);
                }}
                className={`w-full text-left px-3 py-2 text-sm hover:bg-accent ${
                  model.id === selectedModel ? "bg-accent font-medium" : ""
                }`}
              >
                <div>{model.name}</div>
                <div className="text-xs text-muted-foreground">{model.provider}</div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
