/** Generic modal dialog using shadcn/ui pattern. */

import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

type ModalSize = "sm" | "md" | "lg" | "xl" | "full";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  size?: ModalSize;
  footer?: ReactNode;
}

const sizeClasses: Record<ModalSize, string> = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
  full: "max-w-[90vw] max-h-[90vh]",
};

export function Modal({ open, onClose, title, children, size = "md", footer }: ModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 animate-in fade-in"
        onClick={onClose}
        onKeyDown={(e) => {
          if (e.key === "Escape") onClose();
        }}
      />

      {/* Content */}
      <div
        className={cn(
          "relative z-10 bg-white dark:bg-gray-900 rounded-xl shadow-2xl w-full mx-4",
          "animate-in zoom-in-95",
          sizeClasses[size],
        )}
      >
        {/* Header */}
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <h2 className="text-lg font-semibold">{title}</h2>
            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-accent text-muted-foreground transition-colors"
            >
              ✕
            </button>
          </div>
        )}

        {/* Body */}
        <div className={cn("px-6 py-4", size === "full" && "overflow-y-auto")}>{children}</div>

        {/* Footer */}
        {footer && <div className="px-6 py-4 border-t flex justify-end gap-2">{footer}</div>}
      </div>
    </div>
  );
}
