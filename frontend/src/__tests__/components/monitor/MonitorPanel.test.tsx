import { renderWithProviders } from "@/__tests__/test-utils";
import { MonitorPanel } from "@/components/monitor/MonitorPanel";
import { t } from "@/i18n";
import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

describe("MonitorPanel", () => {
  // ---- existing behavior preserved (uncontrolled) ----
  it('renders performance content by default for <MonitorPanel variant="compact" />: 硬件监控, GPU显存, 系统内存', () => {
    renderWithProviders(<MonitorPanel variant="compact" />);
    expect(screen.getByText("硬件监控")).toBeInTheDocument();
    expect(screen.getByText("GPU显存")).toBeInTheDocument();
    expect(screen.getByText("系统内存")).toBeInTheDocument();
  });

  it("renders 近期活动 and agents 数字主管, 风控顾问, 数据专家", () => {
    renderWithProviders(<MonitorPanel variant="compact" />);
    expect(screen.getByText("近期活动")).toBeInTheDocument();
    expect(screen.getByText("数字主管")).toBeInTheDocument();
    expect(screen.getByText("风控顾问")).toBeInTheDocument();
    expect(screen.getByText("数据专家")).toBeInTheDocument();
  });

  it("uncontrolled compact switches to security when clicking button 安全 and shows translated rate limits, requests, and audit events", () => {
    renderWithProviders(<MonitorPanel variant="compact" />);
    fireEvent.click(screen.getByText(t("shell.security")));
    expect(screen.getByText(t("shell.rateLimits"))).toBeInTheDocument();
    expect(screen.getByText(t("shell.apiRequests"))).toBeInTheDocument();
    expect(screen.getByText(t("monitor.llmRequests"))).toBeInTheDocument();
    expect(screen.getByText(t("shell.recentAuditEvents"))).toBeInTheDocument();
  });

  it("controlled visible tabs call onActiveTabChange without changing displayed content until parent updates", () => {
    const onActiveTabChange = vi.fn();
    renderWithProviders(
      <MonitorPanel
        variant="compact"
        activeTab="performance"
        onActiveTabChange={onActiveTabChange}
      />,
    );

    fireEvent.click(screen.getByRole("tab", { name: t("shell.security") }));

    expect(onActiveTabChange).toHaveBeenCalledWith("security");
    expect(screen.getByText(t("shell.hardwareMonitor"))).toBeInTheDocument();
    expect(screen.queryByText(t("shell.rateLimits"))).not.toBeInTheDocument();
  });

  it("adds tab semantics to visible tab controls", () => {
    renderWithProviders(<MonitorPanel variant="compact" />);

    expect(screen.getByRole("tablist")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: t("shell.performance") })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("tab", { name: t("shell.security") })).toHaveAttribute(
      "aria-selected",
      "false",
    );
  });

  it("renders accessible progress bars with clamped rounded values and zero-total guard", () => {
    renderWithProviders(<MonitorPanel variant="compact" />, {
      preloadedState: {
        monitor: {
          activeTab: "performance",
          hardware: {
            cpu_percent: 0,
            memory_used_mb: 256,
            memory_total_mb: 0,
            gpu_utilization_percent: 137.8,
          },
          agentActivities: [],
          containers: [],
          rateLimits: {
            api_requests_per_min: 0,
            llm_requests_per_min: 0,
          },
          auditEvents: [],
          isConnected: false,
          error: null,
        },
      },
    });

    expect(screen.getByRole("progressbar", { name: t("shell.gpuMemory") })).toHaveAttribute(
      "aria-valuenow",
      "100",
    );
    expect(screen.getByRole("progressbar", { name: t("shell.systemMemory") })).toHaveAttribute(
      "aria-valuenow",
      "0",
    );
    expect(screen.queryByText("14.2/32G")).not.toBeInTheDocument();
  });

  it("renders custom memory detail from Redux hardware stats", () => {
    renderWithProviders(<MonitorPanel variant="compact" />, {
      preloadedState: {
        monitor: {
          activeTab: "performance",
          hardware: {
            cpu_percent: 0,
            memory_used_mb: 16384,
            memory_total_mb: 32768,
            gpu_utilization_percent: 50,
          },
          agentActivities: [],
          containers: [],
          rateLimits: {
            api_requests_per_min: 0,
            llm_requests_per_min: 0,
          },
          auditEvents: [],
          isConnected: false,
          error: null,
        },
      },
    });

    expect(screen.getByText("16.0G / 32.0G")).toBeInTheDocument();
  });

  it("does not show stale prototype GPU detail when Redux hardware lacks gpu_name", () => {
    renderWithProviders(<MonitorPanel variant="compact" />, {
      preloadedState: {
        monitor: {
          activeTab: "performance",
          hardware: {
            cpu_percent: 0,
            memory_used_mb: 5120,
            memory_total_mb: 20480,
            gpu_utilization_percent: 73,
          },
          agentActivities: [],
          containers: [],
          rateLimits: {
            api_requests_per_min: 0,
            llm_requests_per_min: 0,
          },
          auditEvents: [],
          isConnected: false,
          error: null,
        },
      },
    });

    expect(screen.queryByText("8.4 / 16G")).not.toBeInTheDocument();
    expect(screen.queryByText("8.4/16G")).not.toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: t("shell.gpuMemory") })).toHaveAttribute(
      "aria-valuenow",
      "73",
    );
  });

  it("renders Redux audit events instead of fallback audit lines in the security tab", () => {
    renderWithProviders(<MonitorPanel variant="compact" activeTab="security" hideTabs />, {
      preloadedState: {
        monitor: {
          activeTab: "performance",
          hardware: null,
          agentActivities: [],
          containers: [],
          rateLimits: {
            api_requests_per_min: 60,
            llm_requests_per_min: 10,
          },
          auditEvents: [
            {
              id: "audit-1",
              action: "REAL_UPLOAD_AUDIT_EVENT",
              user_id: "user-real",
              details: "uploaded.csv validated",
              timestamp: "2026-06-10T12:34:00.000Z",
            },
          ],
          isConnected: true,
          error: null,
        },
      },
    });

    expect(screen.getByText(/REAL_UPLOAD_AUDIT_EVENT/)).toBeInTheDocument();
    expect(screen.queryByText(t("monitor.audit.uploadFile"))).not.toBeInTheDocument();
  });

  // ---- controlled prop behavior ----
  it('controlled security: <MonitorPanel variant="compact" activeTab="security" hideTabs /> shows translated rate limits and does not render button 性能', () => {
    renderWithProviders(<MonitorPanel variant="compact" activeTab="security" hideTabs />);
    expect(screen.getByText(t("shell.rateLimits"))).toBeInTheDocument();
    expect(screen.queryByText(t("shell.performance"))).not.toBeInTheDocument();
  });
});
