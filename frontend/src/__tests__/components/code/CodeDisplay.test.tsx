import { CodeBlock, CodeEditorPanel, ProgressBar } from "@/components/code/CodeDisplay";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock clipboard API
const mockWriteText = vi.fn().mockResolvedValue(undefined);
Object.defineProperty(navigator, "clipboard", {
  value: { writeText: mockWriteText },
  writable: true,
});

describe("CodeBlock", () => {
  const sampleCode = `def hello():
    # This is a comment
    print("Hello, World!")
    return 42`;

  beforeEach(() => {
    mockWriteText.mockClear();
  });

  it("renders code with line numbers", () => {
    render(<CodeBlock code={sampleCode} language="python" />);
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("shows language label in header", () => {
    render(<CodeBlock code={sampleCode} language="python" />);
    expect(screen.getByText("python")).toBeInTheDocument();
  });

  it("shows default language when not specified", () => {
    render(<CodeBlock code="hello" />);
    expect(screen.getByText("python")).toBeInTheDocument();
  });

  it("copy button triggers clipboard.writeText", () => {
    render(<CodeBlock code={sampleCode} />);
    fireEvent.click(screen.getByTitle("Copy"));
    expect(mockWriteText).toHaveBeenCalledWith(sampleCode);
  });

  it("shows checkmark after copy", async () => {
    render(<CodeBlock code={sampleCode} />);
    fireEvent.click(screen.getByTitle("Copy"));
    await waitFor(() => {
      expect(screen.getByText("✓")).toBeInTheDocument();
    });
  });

  it("hides line numbers when showLineNumbers is false", () => {
    render(<CodeBlock code={sampleCode} showLineNumbers={false} />);
    expect(screen.queryByText("1")).not.toBeInTheDocument();
  });

  it("edit button toggles editable textarea", () => {
    render(<CodeBlock code={sampleCode} />);
    fireEvent.click(screen.getByTitle("Edit"));
    expect(screen.getByText("Editing")).toBeInTheDocument();
    fireEvent.click(screen.getByTitle("Edit"));
    expect(screen.queryByText("Editing")).not.toBeInTheDocument();
  });

  it("expand/collapse toggle", () => {
    render(<CodeBlock code={sampleCode} />);
    fireEvent.click(screen.getByTitle("Expand"));
    expect(screen.getByTitle("Collapse")).toBeInTheDocument();
  });

  it("only shows specified actions", () => {
    render(<CodeBlock code={sampleCode} actions={["copy", "run"]} />);
    expect(screen.getByTitle("Copy")).toBeInTheDocument();
    expect(screen.getByTitle("Run")).toBeInTheDocument();
    expect(screen.queryByTitle("Edit")).not.toBeInTheDocument();
    expect(screen.queryByTitle("Download")).not.toBeInTheDocument();
  });

  it("run button logs to console", () => {
    const consoleSpy = vi.spyOn(console, "log").mockImplementation(() => {});
    render(<CodeBlock code={sampleCode} />);
    fireEvent.click(screen.getByTitle("Run"));
    expect(consoleSpy).toHaveBeenCalledWith("Running code:", sampleCode);
    consoleSpy.mockRestore();
  });

  it("download button logs to console", () => {
    const consoleSpy = vi.spyOn(console, "log").mockImplementation(() => {});
    render(<CodeBlock code={sampleCode} />);
    fireEvent.click(screen.getByTitle("Download"));
    expect(consoleSpy).toHaveBeenCalledWith("Downloading...");
    consoleSpy.mockRestore();
  });
});

describe("ProgressBar", () => {
  it("renders with correct width percentage", () => {
    const { container } = render(<ProgressBar progress={65} />);
    const bar = container.querySelector("[style*='width']") as HTMLElement;
    expect(bar).toBeDefined();
    expect(bar.style.width).toBe("65%");
  });

  it("renders label and percentage when label is provided", () => {
    render(<ProgressBar progress={75} label="Loading" />);
    expect(screen.getByText("Loading")).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();
  });

  it("renders label without percentage when showPercentage is false", () => {
    render(<ProgressBar progress={75} label="Loading" showPercentage={false} />);
    expect(screen.getByText("Loading")).toBeInTheDocument();
    expect(screen.queryByText("75%")).not.toBeInTheDocument();
  });

  it("renders blue bar for running status", () => {
    const { container } = render(<ProgressBar progress={30} status="running" />);
    const bar = container.querySelector("[style*='width']") as HTMLElement;
    expect(bar).toHaveClass("bg-blue-500");
  });

  it("renders green bar for completed status", () => {
    const { container } = render(<ProgressBar progress={100} status="completed" />);
    const bar = container.querySelector("[style*='width']") as HTMLElement;
    expect(bar).toHaveClass("bg-green-500");
  });

  it("renders red bar for error status", () => {
    const { container } = render(<ProgressBar progress={50} status="error" />);
    const bar = container.querySelector("[style*='width']") as HTMLElement;
    expect(bar).toHaveClass("bg-red-500");
  });

  it("clamps progress to 0 minimum", () => {
    const { container } = render(<ProgressBar progress={-10} />);
    const bar = container.querySelector("[style*='width']") as HTMLElement;
    expect(bar.style.width).toBe("0%");
  });

  it("clamps progress to 100 maximum", () => {
    const { container } = render(<ProgressBar progress={150} />);
    const bar = container.querySelector("[style*='width']") as HTMLElement;
    expect(bar.style.width).toBe("100%");
  });

  it("rounds percentage display", () => {
    render(<ProgressBar progress={33.7} label="Progress" />);
    expect(screen.getByText("34%")).toBeInTheDocument();
  });
});

describe("CodeEditorPanel", () => {
  const initialCode = "print('hello')";
  const onClose = vi.fn();

  beforeEach(() => {
    onClose.mockClear();
  });

  it("renders with initial code", () => {
    render(<CodeEditorPanel initialCode={initialCode} onClose={onClose} />);
    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveValue(initialCode);
  });

  it("renders toolbar buttons", () => {
    render(<CodeEditorPanel initialCode={initialCode} onClose={onClose} />);
    expect(screen.getByText("Run")).toBeInTheDocument();
    expect(screen.getByText("Copy")).toBeInTheDocument();
    expect(screen.getByText("Close")).toBeInTheDocument();
  });

  it("close button calls onClose", () => {
    render(<CodeEditorPanel initialCode={initialCode} onClose={onClose} />);
    fireEvent.click(screen.getByText("Close"));
    expect(onClose).toHaveBeenCalled();
  });

  it("textarea editing updates code", () => {
    render(<CodeEditorPanel initialCode={initialCode} onClose={onClose} />);
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "new code" } });
    expect(textarea).toHaveValue("new code");
  });

  it("shows line count and character count in status bar", () => {
    const code = "line1\nline2\nline3"; // actual newlines in JS string
    const { container } = render(<CodeEditorPanel initialCode={code} onClose={onClose} />);
    // Splitting by newline gives 3 lines, 17 characters
    expect(container.textContent).toContain("3 lines");
    expect(container.textContent).toContain("17 characters");
  });

  it("shows language in title bar", () => {
    render(<CodeEditorPanel initialCode={initialCode} language="typescript" onClose={onClose} />);
    expect(screen.getByText(/typescript/)).toBeInTheDocument();
  });
});
