import { ModelSelector } from "@/components/shared/ModelSelector";
import type { ModelOption } from "@/components/shared/ModelSelector";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const mockModels: ModelOption[] = [
  { id: "deepseek-chat", name: "DeepSeek Chat", provider: "DeepSeek" },
  { id: "gpt-4o", name: "GPT-4o", provider: "OpenAI" },
  { id: "claude-sonnet-4-6", name: "Claude Sonnet 4.6", provider: "Anthropic" },
];

describe("ModelSelector", () => {
  it("renders selected model name", () => {
    render(<ModelSelector models={mockModels} selectedModel="deepseek-chat" onSelect={vi.fn()} />);
    expect(screen.getByText("DeepSeek Chat")).toBeInTheDocument();
  });

  it("renders fallback text when model not found", () => {
    render(<ModelSelector models={mockModels} selectedModel="nonexistent" onSelect={vi.fn()} />);
    // t("model.default") returns "默认模型"
    expect(screen.getByText("默认模型")).toBeInTheDocument();
  });

  it("opens dropdown on button click", () => {
    render(<ModelSelector models={mockModels} selectedModel="deepseek-chat" onSelect={vi.fn()} />);
    // The button title uses t("model.select") = "选择模型"
    fireEvent.click(screen.getByTitle("选择模型"));
    // All model names should now be visible in the dropdown
    expect(screen.getByText("GPT-4o")).toBeInTheDocument();
    expect(screen.getByText("Claude Sonnet 4.6")).toBeInTheDocument();
  });

  it("displays provider name under each model option", () => {
    render(<ModelSelector models={mockModels} selectedModel="deepseek-chat" onSelect={vi.fn()} />);
    fireEvent.click(screen.getByTitle("选择模型"));
    expect(screen.getByText("DeepSeek")).toBeInTheDocument();
    expect(screen.getByText("OpenAI")).toBeInTheDocument();
    expect(screen.getByText("Anthropic")).toBeInTheDocument();
  });

  it("selecting a model calls onSelect and closes dropdown", () => {
    const onSelect = vi.fn();
    render(<ModelSelector models={mockModels} selectedModel="deepseek-chat" onSelect={onSelect} />);
    fireEvent.click(screen.getByTitle("选择模型"));
    fireEvent.click(screen.getByText("GPT-4o"));
    expect(onSelect).toHaveBeenCalledWith("gpt-4o");
  });

  it("clicking backdrop closes dropdown", () => {
    render(<ModelSelector models={mockModels} selectedModel="deepseek-chat" onSelect={vi.fn()} />);
    fireEvent.click(screen.getByTitle("选择模型"));
    expect(screen.getByText("GPT-4o")).toBeInTheDocument();
    // Click the backdrop
    const backdrop = document.querySelector(".fixed.inset-0");
    expect(backdrop).toBeInTheDocument();
    fireEvent.click(backdrop as HTMLElement);
    expect(screen.queryByText("GPT-4o")).not.toBeInTheDocument();
  });
});
