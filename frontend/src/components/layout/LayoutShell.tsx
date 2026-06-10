import { AgentManagerUI } from "@/components/agent/AgentManagerUI";
import { AssetPanel } from "@/components/asset/AssetPanel";
import {
  ConversationSidebar,
} from "@/components/conversation/ConversationUI";
import { MonitorPanel } from "@/components/monitor/MonitorPanel";
import { t } from "@/i18n";
import { Circle, Maximize2, Minus, PanelLeft, PanelRight, Square } from "lucide-react";
import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";

const leftTabs = [
  { id: "conversations", label: t("nav.conversations") },
  { id: "assets", label: t("nav.assets") },
] as const;

const rightTabs = [
  { id: "performance", label: t("shell.performance") },
  { id: "security", label: t("shell.security") },
  { id: "agent", label: t("shell.agent") },
] as const;

type LeftTab = (typeof leftTabs)[number]["id"];
type RightTab = (typeof rightTabs)[number]["id"];

function tabClass(active: boolean) {
  return `flex-1 border-b-2 px-3 py-2 text-xs font-medium transition-colors ${
    active
      ? "border-blue-600 bg-white text-blue-700"
      : "border-transparent bg-slate-100 text-slate-500 hover:bg-white hover:text-slate-900"
  }`;
}

export function LayoutShell() {
  const [leftTab, setLeftTab] = useState<LeftTab>("conversations");
  const [rightTab, setRightTab] = useState<RightTab>("performance");

  const handleLeftTab = (tab: LeftTab) => {
    setLeftTab(tab);
  };

  const handleRightTab = (tab: RightTab) => {
    setRightTab(tab);
  };

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-slate-100 text-slate-900">
      <header className="flex h-10 shrink-0 items-center gap-3 bg-blue-600 px-3 text-white shadow-sm">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <Circle aria-hidden="true" className="fill-white/90" size={10} />
          <span>{t("shell.product")}</span>
          <span className="rounded bg-blue-500 px-1.5 py-0.5 text-[10px] font-medium">
            {t("shell.version")}
          </span>
        </div>
        <div className="mx-auto flex items-center gap-2 text-sm font-semibold tracking-wide">
          <PanelLeft aria-hidden="true" size={15} />
          <span>{t("shell.workspace")}</span>
          <PanelRight aria-hidden="true" size={15} />
        </div>
        <div className="flex items-center gap-2 text-white/85">
          <Minus aria-hidden="true" size={14} />
          <Square aria-hidden="true" size={12} />
          <Maximize2 aria-hidden="true" size={13} />
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <aside className="hidden w-[24%] shrink-0 flex-col border-r border-slate-200 bg-white md:flex">
          <div
            className="flex shrink-0 border-b border-slate-200 bg-slate-100"
            role="tablist"
            aria-label="左侧工作区"
          >
            {leftTabs.map((tab) => {
              const isSelected = leftTab === tab.id;

              return (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={isSelected}
                  onClick={() => handleLeftTab(tab.id)}
                  className={tabClass(isSelected)}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>
          <div className="min-h-0 flex-1 overflow-hidden" role="tabpanel">
            {leftTab === "conversations" ? (
              <ConversationSidebar />
            ) : (
              <AssetPanel variant="compact" />
            )}
          </div>
        </aside>

        <main className="min-w-0 flex-1 bg-white">
          <Outlet />
        </main>

        <aside className="hidden w-[16%] shrink-0 flex-col border-l border-slate-200 bg-white xl:flex">
          <div
            className="flex shrink-0 border-b border-slate-200 bg-slate-100"
            role="tablist"
            aria-label="右侧工作区"
          >
            {rightTabs.map((tab) => {
              const isSelected = rightTab === tab.id;

              return (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={isSelected}
                  onClick={() => handleRightTab(tab.id)}
                  className={tabClass(isSelected)}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>
          <div className="min-h-0 flex-1 overflow-auto" role="tabpanel">
            {rightTab === "performance" && (
              <MonitorPanel variant="compact" activeTab="performance" hideTabs />
            )}
            {rightTab === "security" && (
              <MonitorPanel variant="compact" activeTab="security" hideTabs />
            )}
            {rightTab === "agent" && <AgentManagerUI variant="compact" />}
          </div>
        </aside>
      </div>

      <footer className="flex h-9 shrink-0 items-center gap-4 border-t border-slate-200 bg-white px-4 text-xs text-slate-600">
        <span>{t("shell.statusApi")}</span>
        <button type="button" className="rounded px-2 py-1 text-blue-600 hover:bg-blue-50">
          {t("shell.exportLogs")}
        </button>
        <span className="ml-auto font-mono text-emerald-600">{t("shell.ping")}</span>
      </footer>
    </div>
  );
}
