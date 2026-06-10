import {
  Toast,
  ToastContainer,
  addToast,
  dismissToast,
  subscribeToToasts,
} from "@/components/shared/Toast";
import type { ToastMessage } from "@/components/shared/Toast";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("Toast", () => {
  const mockOnDismiss = vi.fn();
  const baseToast: ToastMessage = {
    id: "test-1",
    type: "info",
    title: "Test Title",
    message: "Test message content",
    duration: 3000,
  };

  beforeEach(() => {
    vi.useFakeTimers();
    mockOnDismiss.mockClear();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders title and message", () => {
    render(<Toast toast={baseToast} onDismiss={mockOnDismiss} />);
    expect(screen.getByText("Test Title")).toBeInTheDocument();
    expect(screen.getByText("Test message content")).toBeInTheDocument();
  });

  it("renders without message", () => {
    const toast: ToastMessage = { id: "t2", type: "success", title: "Success!" };
    render(<Toast toast={toast} onDismiss={mockOnDismiss} />);
    expect(screen.getByText("Success!")).toBeInTheDocument();
  });

  it("renders success color class", () => {
    const toast: ToastMessage = { id: "t3", type: "success", title: "OK" };
    const { container } = render(<Toast toast={toast} onDismiss={mockOnDismiss} />);
    expect(container.firstChild).toHaveClass("border-green-500");
  });

  it("renders error color class", () => {
    const toast: ToastMessage = { id: "t4", type: "error", title: "Error" };
    const { container } = render(<Toast toast={toast} onDismiss={mockOnDismiss} />);
    expect(container.firstChild).toHaveClass("border-red-500");
  });

  it("renders warning color class", () => {
    const toast: ToastMessage = { id: "t5", type: "warning", title: "Warn" };
    const { container } = render(<Toast toast={toast} onDismiss={mockOnDismiss} />);
    expect(container.firstChild).toHaveClass("border-yellow-500");
  });

  it("renders info color class", () => {
    const toast: ToastMessage = { id: "t6", type: "info", title: "Info" };
    const { container } = render(<Toast toast={toast} onDismiss={mockOnDismiss} />);
    expect(container.firstChild).toHaveClass("border-blue-500");
  });

  it("auto-dismisses after duration", () => {
    render(<Toast toast={baseToast} onDismiss={mockOnDismiss} />);
    act(() => {
      vi.advanceTimersByTime(3000);
    });
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(mockOnDismiss).toHaveBeenCalledWith("test-1");
  });

  it("uses default 4000ms duration when not specified", () => {
    const toast: ToastMessage = { id: "t7", type: "info", title: "Default duration" };
    render(<Toast toast={toast} onDismiss={mockOnDismiss} />);
    act(() => {
      vi.advanceTimersByTime(4299);
    });
    expect(mockOnDismiss).not.toHaveBeenCalled();
    act(() => {
      vi.advanceTimersByTime(2);
    });
    expect(mockOnDismiss).toHaveBeenCalledWith("t7");
  });

  it("manual dismiss via close button", () => {
    render(<Toast toast={baseToast} onDismiss={mockOnDismiss} />);
    fireEvent.click(screen.getByText("×"));
    expect(mockOnDismiss).toHaveBeenCalledWith("test-1");
  });
});

describe("ToastContainer", () => {
  it("renders multiple toasts", () => {
    const toasts: ToastMessage[] = [
      { id: "a", type: "info", title: "First" },
      { id: "b", type: "success", title: "Second" },
      { id: "c", type: "error", title: "Third" },
    ];
    render(<ToastContainer toasts={toasts} onDismiss={vi.fn()} />);
    expect(screen.getByText("First")).toBeInTheDocument();
    expect(screen.getByText("Second")).toBeInTheDocument();
    expect(screen.getByText("Third")).toBeInTheDocument();
  });

  it("renders empty when no toasts", () => {
    const { container } = render(<ToastContainer toasts={[]} onDismiss={vi.fn()} />);
    expect(container.firstChild?.childNodes.length).toBe(0);
  });
});

describe("Toast Manager (event-based)", () => {
  // The addToast/subscribeToToasts/dismissToast functions operate on
  // module-level state. We test them by integrating with the ToastContainer
  // component pattern — the key contract is:
  //   1. addToast() pushes to the state
  //   2. subscribeToToasts() notifies subscribers
  //   3. dismissToast() removes from the state

  it("addToast, subscribeToToasts, and dismissToast work together", () => {
    const received: ToastMessage[][] = [];
    // Subscribe to capture state changes
    const unsub = subscribeToToasts((toasts) => {
      received.push([...toasts]);
    });

    // Initial callback fires on subscribe — clear it
    const initialCount = received.length;

    // Add a toast
    addToast({ type: "success", title: "Integration Test" });
    expect(received.length).toBe(initialCount + 1);
    const lastState = received[received.length - 1];
    const added = lastState.find((t) => t.title === "Integration Test");
    expect(added).toBeDefined();
    expect(added?.id).toMatch(/^toast-/);

    // Dismiss it
    // biome-ignore lint/style/noNonNullAssertion: guarded by expect(added).toBeDefined() above
    dismissToast(added!.id);
    expect(received.length).toBe(initialCount + 2);
    const afterDismiss = received[received.length - 1];
    // biome-ignore lint/style/noNonNullAssertion: guarded by expect(added).toBeDefined() above
    expect(afterDismiss.find((t) => t.id === added!.id)).toBeUndefined();

    // Unsubscribe
    unsub();

    // Clean up: dismiss any remaining toasts
    const finalState = afterDismiss;
    for (const t of finalState) {
      dismissToast(t.id);
    }
  });

  it("addToast creates toast with unique ID per call", () => {
    const received: ToastMessage[][] = [];
    const unsub = subscribeToToasts((toasts) => {
      received.push([...toasts]);
    });
    // clear initial
    received.length = 0;

    addToast({ type: "info", title: "First" });
    addToast({ type: "info", title: "Second" });

    const lastState = received[received.length - 1];
    const firsts = lastState.filter((t) => t.title === "First");
    const seconds = lastState.filter((t) => t.title === "Second");
    expect(firsts.length).toBe(1);
    expect(seconds.length).toBe(1);
    expect(firsts[0].id).not.toBe(seconds[0].id);

    // Cleanup
    unsub();
    for (const t of lastState) {
      dismissToast(t.id);
    }
  });
});
