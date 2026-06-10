/** Toast notification component. */

import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";

export interface ToastMessage {
  id: string;
  type: "success" | "error" | "info" | "warning";
  title: string;
  message?: string;
  duration?: number;
}

interface ToastProps {
  toast: ToastMessage;
  onDismiss: (id: string) => void;
}

export function Toast({ toast, onDismiss }: ToastProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));

    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(() => onDismiss(toast.id), 300);
    }, toast.duration ?? 4000);

    return () => clearTimeout(timer);
  }, [toast.id, toast.duration, onDismiss]);

  const colorClasses = {
    success: "border-green-500 bg-green-50 dark:bg-green-950",
    error: "border-red-500 bg-red-50 dark:bg-red-950",
    info: "border-blue-500 bg-blue-50 dark:bg-blue-950",
    warning: "border-yellow-500 bg-yellow-50 dark:bg-yellow-950",
  };

  return (
    <div
      className={cn(
        "border-l-4 rounded-lg shadow-lg p-3 min-w-[280px] max-w-sm transition-all duration-300",
        colorClasses[toast.type],
        visible ? "opacity-100 translate-x-0" : "opacity-0 translate-x-4",
      )}
    >
      <div className="flex justify-between items-start">
        <div>
          <p className="font-medium text-sm">{toast.title}</p>
          {toast.message && <p className="text-xs text-muted-foreground mt-1">{toast.message}</p>}
        </div>
        <button
          type="button"
          onClick={() => onDismiss(toast.id)}
          className="text-muted-foreground hover:text-foreground ml-2"
        >
          ×
        </button>
      </div>
    </div>
  );
}

// Toast container
interface ToastContainerProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

// Toast manager (simple event-based)
let toastSubscribers: Array<(toasts: ToastMessage[]) => void> = [];
let currentToasts: ToastMessage[] = [];

export function addToast(toast: Omit<ToastMessage, "id">): void {
  const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const newToast: ToastMessage = { ...toast, id };
  currentToasts = [...currentToasts, newToast];
  for (const fn of toastSubscribers) fn(currentToasts);
}

export function subscribeToToasts(fn: (toasts: ToastMessage[]) => void): () => void {
  toastSubscribers.push(fn);
  return () => {
    toastSubscribers = toastSubscribers.filter((s) => s !== fn);
  };
}

export function dismissToast(id: string): void {
  currentToasts = currentToasts.filter((t) => t.id !== id);
  for (const fn of toastSubscribers) fn(currentToasts);
}
