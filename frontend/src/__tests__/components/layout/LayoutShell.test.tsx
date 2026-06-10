import { renderWithProviders } from "@/__tests__/test-utils";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { fireEvent, screen } from "@testing-library/react";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { describe, expect, it } from "vitest";

function RouteDriver({ to }: { to: string }) {
  const navigate = useNavigate();

  useEffect(() => {
    navigate(to);
  }, [navigate, to]);

  return null;
}

describe("LayoutShell", () => {
  it("renders the prototype title bar", () => {
    renderWithProviders(<LayoutShell />);

    expect(screen.getByText("DeepSeek")).toBeInTheDocument();
    expect(screen.getByText("V6.2.0")).toBeInTheDocument();
    expect(screen.getByText("NEXUS AI")).toBeInTheDocument();
  });

  it("renders left workspace tabs", () => {
    renderWithProviders(<LayoutShell />);

    expect(screen.getByRole("tab", { name: "会话" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "资产" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /新建对话/ })).toBeInTheDocument();
  });

  it("switches the left panel to assets", () => {
    renderWithProviders(<LayoutShell />);

    fireEvent.click(screen.getByRole("tab", { name: "资产" }));

    expect(screen.getByPlaceholderText("搜索...")).toBeInTheDocument();
    expect(screen.getByText("sales_report.csv")).toBeInTheDocument();
  });

  it("renders center conversation workspace", () => {
    renderWithProviders(<LayoutShell />);

    expect(screen.getByText(/建议：建议主攻/)).toBeInTheDocument();
    expect(screen.getByText("spider_probe_server.py")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("输入您的问题...")).toBeInTheDocument();
  });

  it("renders right workspace tabs and switches to Agent", () => {
    renderWithProviders(<LayoutShell />);

    expect(screen.getByRole("tab", { name: "性能" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "安全" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Agent" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Agent" }));

    expect(screen.getByText("数字主管")).toBeInTheDocument();
    expect(screen.getByText("风控顾问")).toBeInTheDocument();
  });

  it("renders bottom status bar", () => {
    renderWithProviders(<LayoutShell />);

    expect(screen.getByText(/DeepSeek API \| API Key已配置/)).toBeInTheDocument();
    expect(screen.getByText("导出日志")).toBeInTheDocument();
    expect(screen.getByText("PING 15ms")).toBeInTheDocument();
  });

  it("activates asset tab from /assets route", () => {
    renderWithProviders(<LayoutShell />, { initialRoute: "/assets" });

    expect(screen.getByRole("tab", { name: "资产" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "会话" })).toHaveAttribute("aria-selected", "false");
    expect(screen.getByText("sales_report.csv")).toBeInTheDocument();
  });

  it("resets stale asset tab state on non-asset routes", () => {
    const { rerender } = renderWithProviders(
      <>
        <RouteDriver to="/assets" />
        <LayoutShell />
      </>,
      { initialRoute: "/assets" },
    );

    expect(screen.getByRole("tab", { name: "资产" })).toHaveAttribute("aria-selected", "true");

    rerender(
      <>
        <RouteDriver to="/conversations" />
        <LayoutShell />
      </>,
    );

    expect(screen.getByRole("tab", { name: "会话" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "资产" })).toHaveAttribute("aria-selected", "false");
  });

  it("activates agent tab from /agents route", () => {
    renderWithProviders(<LayoutShell />, { initialRoute: "/agents" });

    expect(screen.getByRole("tab", { name: "Agent" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "性能" })).toHaveAttribute("aria-selected", "false");
    expect(screen.getByText("数字主管")).toBeInTheDocument();
    expect(screen.getByText("风控顾问")).toBeInTheDocument();
  });

  it("resets stale agent tab state on non-agent routes", () => {
    const { rerender } = renderWithProviders(
      <>
        <RouteDriver to="/agents" />
        <LayoutShell />
      </>,
      { initialRoute: "/agents" },
    );

    expect(screen.getByRole("tab", { name: "Agent" })).toHaveAttribute("aria-selected", "true");

    rerender(
      <>
        <RouteDriver to="/assets" />
        <LayoutShell />
      </>,
    );

    expect(screen.getByRole("tab", { name: "性能" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "Agent" })).toHaveAttribute("aria-selected", "false");
  });

  it("activates performance tab from /monitor route", () => {
    renderWithProviders(<LayoutShell />, { initialRoute: "/monitor" });

    expect(screen.getByRole("tab", { name: "性能" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "Agent" })).toHaveAttribute("aria-selected", "false");
    expect(screen.getByText("硬件监控")).toBeInTheDocument();
    expect(screen.getByText("GPU显存")).toBeInTheDocument();
  });
});
