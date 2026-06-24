import React from "react";
import type { OrchestrationPlan, PlanStep } from "../../features/conversation/conversationSlice";

interface PlanViewerProps {
  plan: OrchestrationPlan;
  isAwaitingApproval: boolean;
  isExecuting: boolean;
  onApprove: () => void;
  onReject: () => void;
  onEdit: (steps: PlanStep[]) => void;
  onPause: () => void;
  onResume: () => void;
  onCancel: () => void;
  onRetryStep: (stepId: string) => void;
}

const STATUS_STYLES: Record<PlanStep["status"], string> = {
  pending: "bg-gray-100 text-gray-500 border-gray-200",
  running: "bg-blue-50 text-blue-700 border-blue-200",
  completed: "bg-green-50 text-green-700 border-green-200",
  failed: "bg-red-50 text-red-700 border-red-200",
  skipped: "bg-yellow-50 text-yellow-600 border-yellow-200",
};

const STATUS_ICONS: Record<PlanStep["status"], string> = {
  pending: "○",
  running: "◑",
  completed: "✓",
  failed: "✗",
  skipped: "⏭",
};

const STATUS_LABELS: Record<PlanStep["status"], string> = {
  pending: "等待",
  running: "执行中",
  completed: "完成",
  failed: "失败",
  skipped: "已跳过",
};

// --- Meta-Agent layer progress indicator ---
const LAYER_LABELS: Record<string, string> = {
  decision: "决策",
  strategy: "策略",
  execution: "执行",
  strategy_review: "审查",
};

const LAYER_ICONS: Record<string, string> = {
  decision: "🎯",
  strategy: "📋",
  execution: "⚙️",
  strategy_review: "🔍",
};

function LayerProgressBar({ layers, currentLayer }: {
  layers?: string[];
  currentLayer?: string | null;
}) {
  if (!layers || layers.length === 0) return null;

  const currentIdx = currentLayer ? layers.indexOf(currentLayer) : -1;

  return (
    <div className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50/50 border-b border-blue-100">
      {layers.map((layer, i) => {
        const isComplete = i < currentIdx;
        const isActive = i === currentIdx;
        const isPending = i > currentIdx;

        return (
          <React.Fragment key={layer}>
            {i > 0 && (
              <span className={`text-[10px] ${isComplete ? "text-green-400" : "text-gray-300"}`}>
                ▸
              </span>
            )}
            <span
              className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                isComplete
                  ? "bg-green-100 text-green-700"
                  : isActive
                    ? "bg-blue-100 text-blue-700 font-medium animate-pulse"
                    : "bg-gray-100 text-gray-400"
              }`}
              title={LAYER_LABELS[layer] ?? layer}
            >
              {LAYER_ICONS[layer] ?? ""} {LAYER_LABELS[layer] ?? layer}
              {isComplete && " ✓"}
            </span>
          </React.Fragment>
        );
      })}
    </div>
  );
}

function StepCard({ step, onRetry }: { step: PlanStep; onRetry: (id: string) => void }) {
  return (
    <div
      className={`rounded-lg border px-3 py-2 text-xs ${STATUS_STYLES[step.status]}`}
      style={{ minWidth: 140, maxWidth: 220 }}
    >
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-sm" title={STATUS_LABELS[step.status]}>
          {STATUS_ICONS[step.status]}
        </span>
        <span className="font-medium truncate">{step.agent_name}</span>
        <span className="text-base">{step.agent_emoji}</span>
      </div>
      <p className="text-[11px] leading-tight text-gray-600 line-clamp-2 mb-1">
        {step.description}
      </p>
      {step.status === "running" && (
        <div className="h-1 w-full bg-blue-100 rounded-full overflow-hidden mt-1">
          <div className="h-full w-2/3 bg-blue-400 rounded-full animate-pulse" />
        </div>
      )}
      {step.status === "failed" && step.error && (
        <p className="text-[10px] text-red-500 truncate mt-1" title={step.error}>
          {step.error}
        </p>
      )}
      {step.status === "failed" && (
        <button
          onClick={() => onRetry(step.step_id)}
          className="mt-1.5 text-[10px] px-2 py-0.5 rounded bg-red-100 hover:bg-red-200 text-red-700 transition-colors"
        >
          重试
        </button>
      )}
    </div>
  );
}

function GroupConnector() {
  return (
    <div className="flex justify-center py-1">
      <svg width="24" height="16" className="text-gray-300">
        <line x1="12" y1="0" x2="12" y2="12" stroke="currentColor" strokeWidth="1.5" />
        <polygon points="6,8 12,16 18,8" fill="currentColor" />
      </svg>
    </div>
  );
}

export function PlanViewer({
  plan,
  isAwaitingApproval,
  isExecuting,
  onApprove,
  onReject,
  onPause,
  onResume,
  onCancel,
  onRetryStep,
}: PlanViewerProps) {
  const groups = plan.parallel_groups ?? [plan.steps.map((s) => s.step_id)];

  // Build step lookup
  const stepMap: Record<string, PlanStep> = {};
  for (const s of plan.steps) {
    stepMap[s.step_id] = s;
  }

  const statusBadge = (() => {
    switch (plan.status) {
      case "awaiting_approval":
        return <span className="px-2 py-0.5 text-[10px] font-medium bg-yellow-100 text-yellow-700 rounded-full">等待审批</span>;
      case "running":
        return <span className="px-2 py-0.5 text-[10px] font-medium bg-blue-100 text-blue-700 rounded-full">执行中</span>;
      case "paused":
        return <span className="px-2 py-0.5 text-[10px] font-medium bg-orange-100 text-orange-700 rounded-full">已暂停</span>;
      case "completed":
        return <span className="px-2 py-0.5 text-[10px] font-medium bg-green-100 text-green-700 rounded-full">已完成</span>;
      case "failed":
        return <span className="px-2 py-0.5 text-[10px] font-medium bg-red-100 text-red-700 rounded-full">失败</span>;
      case "cancelled":
        return <span className="px-2 py-0.5 text-[10px] font-medium bg-gray-200 text-gray-600 rounded-full">已取消</span>;
      default:
        return <span className="px-2 py-0.5 text-[10px] font-medium bg-gray-100 text-gray-600 rounded-full">就绪</span>;
    }
  })();

  return (
    <div className="my-2 border border-gray-200 rounded-lg bg-white shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-sm font-semibold text-gray-800 truncate">
            📋 {plan.title}
          </span>
          {statusBadge}
        </div>
        <span className="text-[10px] text-gray-400 flex-shrink-0 ml-2">
          {plan.steps.length} 步骤
        </span>
      </div>

      {/* Layer progress bar */}
      <LayerProgressBar
        layers={plan.meta_agent_layers}
        currentLayer={null}
      />

      {/* Approval buttons */}
      {isAwaitingApproval && (
        <div className="flex items-center gap-2 px-3 py-2 bg-yellow-50 border-b border-yellow-100">
          <button
            onClick={onApprove}
            className="px-3 py-1 text-xs font-medium bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
          >
            ✓ 批准执行
          </button>
          <button
            onClick={onReject}
            className="px-3 py-1 text-xs font-medium bg-white text-red-600 border border-red-300 rounded hover:bg-red-50 transition-colors"
          >
            ✗ 拒绝
          </button>
          <span className="text-[10px] text-yellow-600 ml-auto">
            请审核计划后再执行
          </span>
        </div>
      )}

      {/* Execution controls */}
      {isExecuting && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 border-b border-blue-100">
          {plan.status === "paused" ? (
            <button
              onClick={onResume}
              className="px-2.5 py-0.5 text-xs font-medium bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
            >
              ▶ 继续
            </button>
          ) : (
            <button
              onClick={onPause}
              className="px-2.5 py-0.5 text-xs font-medium bg-yellow-500 text-white rounded hover:bg-yellow-600 transition-colors"
            >
              ⏸ 暂停
            </button>
          )}
          <button
            onClick={onCancel}
            className="px-2.5 py-0.5 text-xs font-medium bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
          >
            ⏹ 取消
          </button>
        </div>
      )}

      {/* Plan DAG visualization */}
      <div className="px-3 py-2 overflow-x-auto">
        {groups.map((group, gi) => (
          <React.Fragment key={`group-${gi}`}>
            {gi > 0 && <GroupConnector />}
            <div className="flex flex-wrap gap-2 justify-center">
              {group.map((stepId) => {
                const step = stepMap[stepId];
                if (!step) return null;
                return <StepCard key={stepId} step={step} onRetry={onRetryStep} />;
              })}
            </div>
            {groups.length > 1 && gi < groups.length - 1 && (
              <div className="text-center text-[10px] text-gray-400 mt-1">↓ 下一阶段</div>
            )}
          </React.Fragment>
        ))}
        {groups.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-2">无执行步骤</p>
        )}
      </div>
    </div>
  );
}
