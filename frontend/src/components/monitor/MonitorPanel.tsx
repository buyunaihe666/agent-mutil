/** Monitor Panel - performance/security tabs, agent activity list. */

import {
  type AgentActivity,
  type HardwareStats,
  setActiveTab,
} from "@/features/monitor/monitorSlice";
import { t } from "@/i18n";
import type { AppDispatch, RootState } from "@/store";
import { useDispatch, useSelector } from "react-redux";

type Tab = "performance" | "security";

export interface MonitorPanelProps {
  variant?: "full" | "compact";
  activeTab?: Tab;
  onActiveTabChange?: (tab: Tab) => void;
  hideTabs?: boolean;
}

const MOCK_HARDWARE: HardwareStats = {
  cpu_percent: 25.5,
  memory_used_mb: 14540.8,
  memory_total_mb: 32768,
  gpu_name: "NVIDIA RTX 4090",
  gpu_utilization_percent: 52.5,
};

const MOCK_ACTIVITIES: AgentActivity[] = [
  {
    agent_id: "1",
    agent_name: t("shell.agentSupervisor"),
    agent_emoji: "🎯",
    status: "working",
    message: t("monitor.activity.coordinatingAgents"),
  },
  {
    agent_id: "2",
    agent_name: t("shell.agentRiskAdvisor"),
    agent_emoji: "🛡️",
    status: "idle",
    message: t("monitor.activity.waitingRiskAssessment"),
  },
  {
    agent_id: "3",
    agent_name: t("shell.agentDataExpert"),
    agent_emoji: "📊",
    status: "idle",
    message: t("monitor.activity.dataAnalysisReady"),
  },
];

const MOCK_AUDIT_EVENTS = [
  t("monitor.audit.executeCode"),
  t("monitor.audit.createConversation"),
  t("monitor.audit.uploadFile"),
  t("monitor.audit.createAgent"),
  t("monitor.audit.archiveConversation"),
];

function formatMbAsGb(mb: number) {
  return `${(mb / 1024).toFixed(1)}G`;
}

function formatMemoryDetail(usedMb: number, totalMb: number) {
  if (totalMb <= 0) {
    return `${usedMb} MB / 0 MB`;
  }

  return `${formatMbAsGb(usedMb)} / ${formatMbAsGb(totalMb)}`;
}

function formatAuditEvent(event: {
  action: string;
  user_id?: string;
  agent_id?: string;
  details?: string;
  timestamp: string;
}) {
  const time = new Date(event.timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
  const actor = event.agent_id ?? event.user_id;
  const suffix = [actor, event.details].filter(Boolean).join(" - ");

  return suffix ? `${time} - ${event.action} (${suffix})` : `${time} - ${event.action}`;
}

function clampProgressValue(value: number) {
  if (!Number.isFinite(value)) {
    return 0;
  }

  return Math.min(100, Math.max(0, value));
}

function progressPercent(used: number, total: number) {
  if (total <= 0) {
    return 0;
  }

  return (used / total) * 100;
}

function statusEmoji(status: string) {
  switch (status) {
    case "working":
      return "🟢";
    case "blocked":
      return "🟡";
    case "error":
      return "🔴";
    default:
      return "⚪";
  }
}

function ProgressRow({
  label,
  detail,
  value,
  color,
}: { label: string; detail: string; value: number; color: string }) {
  const clamped = clampProgressValue(value);
  const rounded = Math.round(clamped);
  return (
    <div>
      <div className="mb-1.5 flex justify-between text-xs">
        <span>{label}</span>
        <span>{detail}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-sidebar-active">
        <div
          className={`h-full rounded-full ${color}`}
          role="progressbar"
          aria-label={label}
          aria-valuenow={rounded}
          aria-valuemin={0}
          aria-valuemax={100}
          tabIndex={0}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}

export function MonitorPanel({
  variant = "full",
  activeTab: controlledActiveTab,
  onActiveTabChange,
  hideTabs = false,
}: MonitorPanelProps) {
  const dispatch = useDispatch<AppDispatch>();
  const {
    activeTab: storeActiveTab,
    hardware: hardwareFromStore,
    agentActivities: activitiesFromStore,
    auditEvents: auditEventsFromStore,
    rateLimits,
  } = useSelector((state: RootState) => state.monitor);

  const activeTab = controlledActiveTab ?? storeActiveTab;
  const hasStoreHardware = hardwareFromStore !== null;
  const hardware = hardwareFromStore ?? MOCK_HARDWARE;
  const activities = activitiesFromStore.length > 0 ? activitiesFromStore : MOCK_ACTIVITIES;
  const auditEvents =
    auditEventsFromStore.length > 0
      ? auditEventsFromStore.map((event) => formatAuditEvent(event))
      : MOCK_AUDIT_EVENTS;
  const isCompact = variant === "compact";

  const handleTabClick = (tab: Tab) => {
    if (controlledActiveTab !== undefined) {
      onActiveTabChange?.(tab);
    } else {
      dispatch(setActiveTab(tab));
    }
  };

  const safeMemoryPercent = progressPercent(hardware.memory_used_mb, hardware.memory_total_mb);
  const gpuUtilizationPercent = hardware.gpu_utilization_percent ?? 0;
  const gpuDetail =
    hardware.gpu_name && hardware.gpu_name.trim().length > 0
      ? hardware.gpu_name
      : hasStoreHardware
        ? `${gpuUtilizationPercent}%`
        : "8.4/16G";
  const memoryDetail = formatMemoryDetail(hardware.memory_used_mb, hardware.memory_total_mb);

  return (
    <div className="h-full flex flex-col bg-sidebar text-white">
      {!hideTabs && (
        <div className="flex border-b border-sidebar-hover" role="tablist">
          {(["performance", "security"] as Tab[]).map((tab) => (
            <button
              key={tab}
              type="button"
              id={`monitor-tab-${tab}`}
              role="tab"
              aria-selected={activeTab === tab}
              onClick={() => handleTabClick(tab)}
              className={`flex-1 py-2 text-xs font-medium transition-colors ${
                activeTab === tab
                  ? "bg-sidebar-active text-white border-b-2 border-blue-500"
                  : "text-white/60 hover:text-white"
              }`}
            >
              {tab === "performance" ? t("shell.performance") : t("shell.security")}
            </button>
          ))}
        </div>
      )}

      <div
        className={`flex-1 overflow-y-auto ${isCompact ? "p-4 space-y-5" : "p-3 space-y-3"} text-xs`}
        role="tabpanel"
        aria-labelledby={hideTabs ? undefined : `monitor-tab-${activeTab}`}
      >
        {activeTab === "performance" && (
          <>
            <div className="space-y-3">
              <h3 className="text-sm font-medium">{t("shell.hardwareMonitor")}</h3>
              <div className="space-y-3">
                <ProgressRow
                  label={t("shell.gpuMemory")}
                  detail={gpuDetail}
                  value={hardware.gpu_utilization_percent ?? 52.5}
                  color="bg-purple-500"
                />
                <ProgressRow
                  label={t("shell.systemMemory")}
                  detail={memoryDetail}
                  value={safeMemoryPercent}
                  color="bg-blue-500"
                />
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-sm font-medium">{t("shell.recentActivity")}</h3>
              {activities.map((act) => (
                <div
                  key={act.agent_id}
                  className="flex items-center gap-2 rounded bg-sidebar-active p-2"
                >
                  <span>{statusEmoji(act.status)}</span>
                  <span>{act.agent_emoji}</span>
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-medium">{act.agent_name}</div>
                    {act.message && <div className="truncate text-white/40">{act.message}</div>}
                  </div>
                  <span className="text-[10px] uppercase text-white/40">{act.status}</span>
                </div>
              ))}
            </div>
          </>
        )}

        {activeTab === "security" && (
          <div className="space-y-3">
            <div>
              <h3 className="mb-2 font-medium uppercase tracking-wide text-white/60">
                {t("shell.rateLimits")}
              </h3>
              <div className="space-y-1 rounded bg-sidebar-active p-2">
                <div className="flex justify-between">
                  <span>{t("shell.apiRequests")}</span>
                  <span className="text-green-400">{rateLimits.api_requests_per_min}/min</span>
                </div>
                <div className="flex justify-between">
                  <span>{t("monitor.llmRequests")}</span>
                  <span className="text-green-400">{rateLimits.llm_requests_per_min}/min</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="mb-2 font-medium uppercase tracking-wide text-white/60">
                {t("shell.recentAuditEvents")}
              </h3>
              <div className="space-y-1 rounded bg-sidebar-active p-2 text-[10px]">
                {auditEvents.map((event) => (
                  <div key={event} className="text-white/60">
                    {event}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
