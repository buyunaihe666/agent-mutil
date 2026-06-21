/** Agent Manager UI - agent list, editor, version history, template library. */

import {
  type AgentData,
  type AgentTemplate,
  addAgent,
  addTemplate,
  removeAgent,
  removeTemplate,
  setActiveTab,
  setAgents,
  setEditingAgent,
  setEditingTemplate,
  setSearchQuery,
  setStatusFilter,
  setTemplateSearchQuery,
  setTemplates,
  updateAgent,
  updateTemplate,
} from "@/features/agent/agentSlice";
import { t } from "@/i18n";
import type { AppDispatch, RootState } from "@/store";
import { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";

interface AgentManagerUIProps {
  variant?: "full" | "compact";
}

type AgentManagerVariant = NonNullable<AgentManagerUIProps["variant"]>;

function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

/* ---------- Agent Card ---------- */
function AgentCard({
  agent,
  onEdit,
  onDelete,
  variant,
}: {
  agent: AgentData;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  variant: AgentManagerVariant;
}) {
  const isCompact = variant === "compact";

  return (
    <div
      className={cx(
        "border rounded-lg bg-white transition-shadow",
        isCompact
          ? "border-gray-200 p-2.5 text-gray-900 shadow-sm hover:shadow-md"
          : "p-4 dark:bg-gray-800 hover:shadow-md",
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex gap-2">
          <div
            className={cx(
              "rounded-full bg-accent flex items-center justify-center shrink-0",
              isCompact ? "w-7 h-7 text-sm" : "w-10 h-10 text-lg",
            )}
          >
            {agent.avatar_emoji ?? "🤖"}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <h3 className={cx("font-medium", isCompact ? "text-xs" : "text-sm")}>
                {agent.name}
              </h3>
              {agent.is_preset && (
                <span className="text-[10px] bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 px-1 py-0.5 rounded">
                  Preset
                </span>
              )}
              {!agent.is_active && (
                <span className="text-[10px] bg-gray-100 dark:bg-gray-700 text-gray-500 px-1 py-0.5 rounded">
                  Inactive
                </span>
              )}
              {agent.is_meta && (
                <span className="ml-1 px-1.5 py-0.5 text-[10px] font-medium bg-purple-100 text-purple-700 rounded-full">
                  Meta
                </span>
              )}
            </div>
            <p className={cx("text-muted-foreground mt-0.5", isCompact ? "text-[10px] line-clamp-1" : "text-xs line-clamp-2")}>
              {agent.description ?? t("status.empty")}
            </p>
          </div>
        </div>
        <div className="flex gap-0.5 shrink-0 ml-1">
          <button
            type="button"
            onClick={() => onEdit(agent.id)}
            className={cx("rounded hover:bg-accent", isCompact ? "text-[10px] px-1 py-0.5" : "text-xs px-2 py-1")}
            title={t("action.edit")}
            aria-label={`${t("action.edit")} ${agent.name}`}
          >
            ✏️
          </button>
          {!agent.is_preset && (
            <button
              type="button"
              onClick={() => onDelete(agent.id)}
              className={cx("rounded hover:bg-red-100 text-red-500", isCompact ? "text-[10px] px-1 py-0.5" : "text-xs px-2 py-1")}
              title={t("action.delete")}
              aria-label={`${t("action.delete")} ${agent.name}`}
            >
              🗑️
            </button>
          )}
        </div>
      </div>
      <div className="mt-2 flex flex-wrap gap-1">
        {(isCompact ? (agent.tools ?? []).slice(0, 2) : agent.tools ?? []).map((tool: string) => (
          <span
            key={tool}
            className={cx(
              "bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-200 rounded",
              isCompact ? "text-[10px] px-1 py-0.5" : "text-xs px-1.5 py-0.5",
            )}
          >
            {tool}
          </span>
        ))}
        {isCompact && (agent.tools ?? []).length > 2 && (
          <span className="text-[10px] text-gray-400">+{(agent.tools ?? []).length - 2}</span>
        )}
      </div>
      {!isCompact && agent.system_prompt && (
        <div className="mt-2 text-xs text-muted-foreground line-clamp-2">
          {agent.system_prompt}
        </div>
      )}
      <div className={cx("flex justify-between text-muted-foreground", isCompact ? "mt-1.5 text-[10px]" : "mt-3 text-xs")}>
        <span>{isCompact ? agent.default_model : `Model: ${agent.default_model}`}</span>
        <span>{isCompact ? `L${agent.permission_level} · v${agent.version_count}` : `Level: L${agent.permission_level} · v${agent.version_count}`}</span>
      </div>
    </div>
  );
}

/* ---------- Agent Editor (Inline) ---------- */
function AgentEditor({
  agent,
  onSave,
  onCancel,
}: {
  agent?: AgentData;
  onSave: (data: Partial<AgentData>) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(agent?.name ?? "");
  const [description, setDescription] = useState(agent?.description ?? "");
  const [systemPrompt, setSystemPrompt] = useState(agent?.system_prompt ?? "");
  const [model, setModel] = useState(agent?.default_model ?? "deepseek-chat");
  const [level, setLevel] = useState(agent?.permission_level ?? 1);
  const [temperature, setTemperature] = useState(agent?.temperature ?? 0.7);
  const [isMeta, setIsMeta] = useState(!!agent?.is_meta);

  return (
    <div className="border rounded-lg p-6 bg-white dark:bg-gray-800 space-y-4">
      <h3 className="font-semibold">{agent ? `${t("action.edit")} Agent` : "New Agent"}</h3>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-medium" htmlFor="agent-name">
            Name
          </label>
          <input
            id="agent-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background"
            placeholder="Agent name"
          />
        </div>
        <div>
          <label className="text-xs font-medium" htmlFor="agent-model">
            Model
          </label>
          <select
            id="agent-model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background"
          >
            <option value="deepseek-chat">DeepSeek Chat</option>
            <option value="deepseek-coder">DeepSeek Coder</option>
            <option value="gpt-4o">GPT-4o</option>
            <option value="claude-sonnet-4-6">Claude Sonnet 4.6</option>
          </select>
        </div>
      </div>

      <div>
        <label className="text-xs font-medium" htmlFor="agent-description">
          Description
        </label>
        <input
          id="agent-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background"
          placeholder="Brief description"
        />
      </div>

      <div>
        <label className="text-xs font-medium" htmlFor="agent-system-prompt">
          System Prompt
        </label>
        <textarea
          id="agent-system-prompt"
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          rows={4}
          className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background resize-none"
          placeholder="Define agent persona, behavior, and output format..."
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-medium" htmlFor="agent-permission-level">
            Permission Level (1-4)
          </label>
          <input
            id="agent-permission-level"
            type="number"
            min={1}
            max={4}
            value={level}
            onChange={(e) => setLevel(Number(e.target.value))}
            className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background"
          />
        </div>
        <div>
          <label className="text-xs font-medium" htmlFor="agent-temperature">
            Temperature ({temperature})
          </label>
          <input
            id="agent-temperature"
            type="range"
            min={0}
            max={2}
            step={0.1}
            value={temperature}
            onChange={(e) => setTemperature(Number(e.target.value))}
            className="w-full mt-1"
          />
        </div>
      </div>

      {/* Meta-Agent checkbox */}
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="is_meta"
          checked={isMeta}
          onChange={(e) => setIsMeta(e.target.checked)}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <label htmlFor="is_meta" className="text-sm text-gray-700 cursor-pointer">
          Meta-Agent (调度者)
        </label>
        <span className="text-[10px] text-gray-400">仅调度其他Agent，不直接执行工具</span>
      </div>

      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm rounded-lg border hover:bg-accent"
        >
          {t("action.cancel")}
        </button>
        <button
          type="button"
          onClick={() =>
            onSave({
              name,
              description,
              system_prompt: systemPrompt,
              default_model: model,
              permission_level: level,
              temperature,
              is_meta: isMeta,
            })
          }
          className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700"
        >
          {t("action.save")}
        </button>
      </div>
    </div>
  );
}

/* ---------- Template Editor (Inline) ---------- */
function TemplateEditor({
  template,
  onSave,
  onCancel,
}: {
  template?: AgentTemplate;
  onSave: (data: Partial<AgentTemplate>) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(template?.name ?? "");
  const [description, setDescription] = useState(template?.description ?? "");
  const [category, setCategory] = useState(template?.category ?? "分析");
  const [systemPrompt, setSystemPrompt] = useState(template?.system_prompt ?? "");
  const [toolsStr, setToolsStr] = useState(template?.tools?.join(", ") ?? "");
  const [avatarEmoji, setAvatarEmoji] = useState(template?.avatar_emoji ?? "🤖");

  return (
    <div className="border rounded-lg p-6 bg-white dark:bg-gray-800 space-y-4">
      <h3 className="font-semibold">
        {template ? `${t("action.edit")} Template` : "New Template"}
      </h3>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-medium" htmlFor="template-name">
            Name
          </label>
          <input
            id="template-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background"
            placeholder="Template name"
          />
        </div>
        <div>
          <label className="text-xs font-medium" htmlFor="template-category">
            Category
          </label>
          <input
            id="template-category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background"
            placeholder="e.g., 分析, 开发, 内容"
          />
        </div>
      </div>

      <div>
        <label className="text-xs font-medium" htmlFor="template-description">
          Description
        </label>
        <input
          id="template-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background"
          placeholder="Brief description"
        />
      </div>

      <div>
        <label className="text-xs font-medium" htmlFor="template-system-prompt">
          System Prompt
        </label>
        <textarea
          id="template-system-prompt"
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          rows={4}
          className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background resize-none"
          placeholder="Define the system prompt for this template..."
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-medium" htmlFor="template-tools">
            Tools (comma-separated)
          </label>
          <input
            id="template-tools"
            value={toolsStr}
            onChange={(e) => setToolsStr(e.target.value)}
            className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background"
            placeholder="file_read, code_execution"
          />
        </div>
        <div>
          <label className="text-xs font-medium" htmlFor="template-emoji">
            Avatar Emoji
          </label>
          <input
            id="template-emoji"
            value={avatarEmoji}
            onChange={(e) => setAvatarEmoji(e.target.value)}
            className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background"
            placeholder="🤖"
          />
        </div>
      </div>

      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm rounded-lg border hover:bg-accent"
        >
          {t("action.cancel")}
        </button>
        <button
          type="button"
          onClick={() =>
            onSave({
              name,
              description,
              category,
              system_prompt: systemPrompt,
              tools: toolsStr
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean),
              avatar_emoji: avatarEmoji,
            })
          }
          className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700"
        >
          {t("action.save")}
        </button>
      </div>
    </div>
  );
}

/* ---------- Template Card ---------- */
function TemplateCard({
  template,
  onUse,
  onEdit,
  onDelete,
  variant,
}: {
  template: AgentTemplate;
  onUse: (tpl: AgentTemplate) => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  variant: AgentManagerVariant;
}) {
  const isCompact = variant === "compact";

  return (
    <div
      className={cx(
        "border rounded-lg bg-white transition-shadow",
        isCompact
          ? "border-gray-200 p-2.5 text-gray-900 shadow-sm hover:shadow-md"
          : "p-4 dark:bg-gray-800 hover:shadow-md",
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex gap-2">
          <div
            className={cx(
              "rounded-full bg-accent flex items-center justify-center shrink-0",
              isCompact ? "w-7 h-7 text-sm" : "w-10 h-10 text-lg",
            )}
          >
            {template.avatar_emoji}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <h3 className={cx("font-medium", isCompact ? "text-xs" : "text-sm")}>
                {template.name}
              </h3>
              <span className={cx("rounded", isCompact ? "text-[10px] bg-blue-50 text-blue-700 px-1 py-0.5" : "text-xs bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-200 px-1.5 py-0.5")}>
                {template.category}
              </span>
            </div>
            <p className={cx("text-muted-foreground mt-0.5", isCompact ? "text-[10px] line-clamp-1" : "text-xs line-clamp-2")}>
              {template.description}
            </p>
          </div>
        </div>
        <div className="flex gap-0.5 shrink-0 ml-1">
          <button
            type="button"
            onClick={() => onEdit(template.id)}
            className={cx("rounded hover:bg-accent", isCompact ? "text-[10px] px-1 py-0.5" : "text-xs px-2 py-1")}
            title={t("action.edit")}
            aria-label={`${t("action.edit")} ${template.name}`}
          >
            ✏️
          </button>
          <button
            type="button"
            onClick={() => onDelete(template.id)}
            className={cx("rounded hover:bg-red-100 text-red-500", isCompact ? "text-[10px] px-1 py-0.5" : "text-xs px-2 py-1")}
            title={t("action.delete")}
            aria-label={`${t("action.delete")} ${template.name}`}
          >
            🗑️
          </button>
          <button
            type="button"
            onClick={() => onUse(template)}
            className={cx("rounded bg-blue-600 text-white hover:bg-blue-700", isCompact ? "text-[10px] px-1.5 py-0.5" : "text-xs px-3 py-1")}
          >
            Use
          </button>
        </div>
      </div>
      <div className="mt-2 flex flex-wrap gap-1">
        {(isCompact ? template.tools.slice(0, 2) : template.tools).map((tool: string) => (
          <span
            key={tool}
            className={cx(
              "bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-200 rounded",
              isCompact ? "text-[10px] px-1 py-0.5" : "text-xs px-1.5 py-0.5",
            )}
          >
            {tool}
          </span>
        ))}
        {isCompact && template.tools.length > 2 && (
          <span className="text-[10px] text-gray-400">+{template.tools.length - 2}</span>
        )}
      </div>
      {!isCompact && (
        <div className="mt-3 flex items-center">
          <span className="text-xs text-muted-foreground line-clamp-2 flex-1">
            {template.system_prompt}
          </span>
        </div>
      )}
    </div>
  );
}

/* ---------- Version History ---------- */
function VersionHistory({
  versions,
}: {
  versions: Array<{ version_number: number; change_description?: string; created_at: string }>;
}) {
  return (
    <div className="space-y-2">
      {versions.map((v) => (
        <div
          key={v.version_number}
          className="flex items-center justify-between text-sm py-1 border-b last:border-b-0"
        >
          <span className="font-mono text-xs">v{v.version_number}</span>
          <span className="text-muted-foreground text-xs">{v.change_description ?? "-"}</span>
          <span className="text-muted-foreground text-xs">
            {new Date(v.created_at).toLocaleDateString()}
          </span>
        </div>
      ))}
    </div>
  );
}

/* ---------- Mock Data ---------- */
const MOCK_AGENTS: AgentData[] = [
  {
    id: "1",
    name: "数字主管",
    description: "任务拆解与分配协调者",
    avatar_emoji: "🎯",
    system_prompt:
      "你是 NEXUS AI 平台的数字主管（Orchestrator），负责统筹协调多个专业 Agent 协同完成复杂任务。\n\n" +
      "## 核心职责\n- 任务分析：理解用户意图，识别隐含需求\n- 任务拆解：将复杂任务分解为可执行的子任务\n- Agent 匹配：根据任务类型选择最合适的执行 Agent\n- 进度管理：跟踪子任务状态，处理异常和阻塞\n- 结果聚合：整合各 Agent 输出为统一回复\n\n" +
      "## 工作流程\n1. 需求分析 → 2. 任务分解（数据层/分析层/产出层）→ 3. Agent 调度 → 4. 质量控制 → 5. 统一输出\n\n" +
      "## 约束\n- 不直接执行代码、查询数据库或写文件\n- 不编造数据或虚构执行结果",
    permission_level: 4,
    is_preset: true,
    is_active: true,
    is_meta: true,
    tools: ["file_read", "agent_communication"],
    default_model: "deepseek-chat",
    temperature: 0.3,
    version_count: 3,
    updated_at: new Date().toISOString(),
  },
  {
    id: "2",
    name: "风控顾问",
    description: "安全审计与合规检查",
    avatar_emoji: "🛡️",
    system_prompt:
      "你是 NEXUS AI 平台的风控顾问，负责对代码执行、数据访问和操作行为进行安全审计与合规检查。\n\n" +
      "## 审计范围\n- 代码安全：注入攻击、命令执行、文件越权\n- 数据合规：越权查询、敏感数据脱敏\n- 操作审计：未授权写入、文件修改、外部通信\n\n" +
      "## 风险评级\n- 🔴 严重：立即阻断 | 🟠 高危：阻止执行 | 🟡 中危：建议修改 | 🔵 低危：建议优化\n\n" +
      "## 约束\n- 只审计不修改\n- 发现敏感数据立即脱敏\n- 参照 OWASP Top 10 / CWE Top 25 / CVSS 3.1",
    permission_level: 3,
    is_preset: true,
    is_active: true,
    tools: ["code_execution_audit", "file_read", "database_query"],
    default_model: "deepseek-chat",
    temperature: 0.2,
    version_count: 2,
    updated_at: new Date().toISOString(),
  },
  {
    id: "3",
    name: "数据专家",
    description: "数据处理与分析",
    avatar_emoji: "📊",
    system_prompt:
      "你是 NEXUS AI 平台的数据专家，精通 SQL 数据分析、Python 统计计算和数据可视化。\n\n" +
      "## 核心技能\n- SQL：复杂查询、窗口函数、多表 JOIN\n- Python：pandas/numpy/scipy 数据处理和统计\n- 可视化：matplotlib 图表生成\n- 信息获取：web_search 外部数据上下文\n\n" +
      "## 工作流程\n1. 需求澄清 → 2. 数据探查（database_query）→ 3. 数据清洗 → 4. 分析计算 → 5. 可视化 → 6. 结论输出\n\n" +
      "## 约束\n- 只读 SQL（SELECT + LIMIT）\n- 敏感数据脱敏\n- 区分相关性与因果性",
    permission_level: 2,
    is_preset: true,
    is_active: true,
    tools: ["database_query", "code_execution", "file_read", "web_search"],
    default_model: "deepseek-chat",
    temperature: 0.4,
    version_count: 1,
    updated_at: new Date().toISOString(),
  },
];

const MOCK_TEMPLATES: AgentTemplate[] = [
  {
    id: "tp1",
    name: "市场分析",
    description: "分析市场趋势、竞品动态、行业报告",
    category: "分析",
    avatar_emoji: "📈",
    system_prompt:
      "你是一位资深市场分析专家，擅长从海量信息中提炼关键洞察。\n\n" +
      "## 工作方法\n1. 明确分析范围 → 2. web_search 收集最新市场数据 → 3. file_read 深入分析数据文件 → 4. code_execution 数据处理和可视化 → 5. 交叉验证 → 6. 提炼洞察\n\n" +
      "## 输出格式\n- 执行摘要（3-5条核心发现）\n- 市场概况（规模、增长率、主要参与者）\n- 趋势分析\n- 竞品格局（SWOT 或对比表格）\n- 机会与风险\n\n" +
      "## 约束\n- 每个结论必须有数据支撑，标注信息来源\n- 区分事实与判断，不确定处标注置信度",
    tools: ["web_search", "file_read", "code_execution"],
  },
  {
    id: "tp2",
    name: "代码审查",
    description: "审查代码质量、安全漏洞、性能优化",
    category: "开发",
    avatar_emoji: "🔍",
    system_prompt:
      "你是一位资深代码审查专家，审查严格但公正，每次给出具体可操作的改进建议。\n\n" +
      "## 审查维度\n1. 安全性：SQL注入、XSS、敏感信息泄露\n2. 正确性：边界条件、空值检查、异常处理\n3. 性能：N+1查询、内存泄漏、阻塞I/O\n4. 可维护性：命名规范、函数复杂度、代码重复\n\n" +
      "## 问题分级\n🔴严重 / 🟠重要 / 🟡一般 / 🔵建议\n\n" +
      "## 输出格式\n- 审查概要 → 问题清单（含Before/After代码示例）→ 代码亮点 → 整体评分（A/B/C/D/F）\n\n" +
      "## 参考标准\nPEP 8 / SOLID / OWASP Top 10",
    tools: ["code_execution", "file_read"],
  },
  {
    id: "tp3",
    name: "文档撰写",
    description: "撰写技术文档、报告、方案",
    category: "内容",
    avatar_emoji: "✍️",
    system_prompt:
      "你是一位专业的技术文档撰写专家，精通将复杂技术概念转化为清晰、准确、结构化的文档。\n\n" +
      "## 文档类型\n- 技术文档：API文档、架构设计、运维手册、README\n- 方案报告：项目方案、技术选型、风险评估\n- 知识库：FAQ、最佳实践、故障排查\n\n" +
      "## 工作方法\n1. 受众分析 → 2. 结构规划 → 3. 内容撰写 → 4. 质量检查 → 5. file_write 输出\n\n" +
      "## 写作原则\n- 一个段落只讲一个主题\n- 专业术语首次出现时解释\n- 用具体例子说明抽象概念\n- 保持中文简洁准确",
    tools: ["file_read", "file_write"],
  },
  {
    id: "tp4",
    name: "数据分析",
    description: "SQL查询、数据清洗、统计分析、图表生成",
    category: "分析",
    avatar_emoji: "📊",
    system_prompt:
      "你是一个数据分析师，擅长SQL查询、数据清洗、统计分析和可视化。请为你的每个分析结论提供数据支持。\n\n" +
      "## 工作方法\n1. 明确分析目标和关键指标\n2. 通过 database_query 探查数据结构\n3. 通过 code_execution 进行数据处理和统计计算\n4. 生成可视化图表辅助理解\n5. 将分析结果翻译为业务洞察\n\n" +
      "## 输出格式\n- 分析摘要（3行以内的核心结论）\n- 数据说明（来源、样本量、时间范围）\n- 关键发现（按重要性排序，每个发现附数据支撑）\n- 行动建议\n- 局限与假设\n\n" +
      "## 约束\n- SQL查询只读（SELECT + LIMIT）\n- 敏感数据脱敏处理\n- 区分相关性与因果性",
    tools: ["database_query", "code_execution", "file_read"],
  },
  {
    id: "tp5",
    name: "安全审计",
    description: "系统安全审计、漏洞扫描、合规检查",
    category: "安全",
    avatar_emoji: "🛡️",
    system_prompt:
      "你是一个安全审计专家，负责检查系统的安全性、合规性和潜在漏洞。请谨慎、严谨地评估每一项风险。\n\n" +
      "## 审计范围\n- 代码安全：注入漏洞、不安全依赖、硬编码密钥\n- 数据安全：访问控制、加密存储、日志审计\n- 合规检查：个保法/GDPR、PCI-DSS、SOC2\n\n" +
      "## 工作方法\n1. 明确审计范围和目标标准\n2. 通过 file_read 审查配置和代码文件\n3. 通过 code_execution_audit 进行代码安全分析\n4. 通过 database_query 检查数据访问日志\n5. 使用 CVSS 3.1 标准评估漏洞严重程度\n6. 形成包含修复优先级的审计报告\n\n" +
      "## 输出格式\n- 审计概要（范围、日期、方法）\n- 执行摘要（面向管理层）\n- 漏洞详表（按 CVSS 评分排列）\n- 风险矩阵\n- 修复路线图（紧急/短期/长期）\n\n" +
      "## 约束\n- 只审计不修改\n- 发现敏感数据立即脱敏\n- 所有操作可追溯",
    tools: ["code_execution_audit", "file_read", "database_query"],
  },
];

/* ---------- Tab bar style helpers ---------- */
function tabButtonClass(active: boolean, isCompact: boolean) {
  return cx(
    "flex-1 py-2 text-xs font-medium transition-colors",
    active
      ? cx(
          "border-b-2 border-blue-500",
          isCompact ? "text-gray-900" : "text-gray-900 dark:text-white",
        )
      : cx(
          "text-gray-500 hover:text-gray-700",
          isCompact ? "" : "dark:text-gray-400 dark:hover:text-white",
        ),
  );
}

/* ---------- Main Agent Manager UI ---------- */
export function AgentManagerUI({ variant = "full" }: AgentManagerUIProps) {
  const isCompact = variant === "compact";
  const dispatch = useDispatch<AppDispatch>();
  const {
    agents: agentsFromStore,
    editingAgentId,
    editingTemplateId,
    activeTab,
    searchQuery,
    templateSearchQuery,
    statusFilter,
    templates: templatesFromStore,
    versionHistory,
  } = useSelector((state: RootState) => state.agent);

  // Fetch agents from backend API on mount to get real UUIDs
  useEffect(() => {
    if (agentsFromStore.length > 0) return;
    const fetchAgents = async () => {
      try {
        const response = await fetch("/api/agents");
        if (response.ok) {
          const data = await response.json();
          if (data && data.length > 0) {
            dispatch(setAgents(data));
          }
        }
      } catch {
        // Silently fail — fallback to mock data
      }
    };
    fetchAgents();
  }, [dispatch, agentsFromStore.length]);

  const [showVersions, setShowVersions] = useState<string | null>(null);

  // Use store data if populated, otherwise fall back to mock data
  const isUsingFallbackAgents = agentsFromStore.length === 0;
  const agents = isUsingFallbackAgents ? MOCK_AGENTS : agentsFromStore;
  const isUsingFallbackTemplates = templatesFromStore.length === 0;
  const templates = isUsingFallbackTemplates ? MOCK_TEMPLATES : templatesFromStore;

  const filtered = agents.filter((a) => {
    if (
      searchQuery &&
      !a.name.includes(searchQuery) &&
      !(a.description ?? "").includes(searchQuery)
    )
      return false;
    if (statusFilter === "active" && !a.is_active) return false;
    if (statusFilter === "inactive" && a.is_active) return false;
    return true;
  });

  const filteredTemplates = templates.filter((tpl) => {
    if (!templateSearchQuery) return true;
    const q = templateSearchQuery.toLowerCase();
    return (
      tpl.name.toLowerCase().includes(q) ||
      tpl.description.toLowerCase().includes(q) ||
      tpl.category.toLowerCase().includes(q)
    );
  });

  const getAgentVersions = (agent: AgentData) => {
    const storedVersions = versionHistory[agent.id];

    if (storedVersions?.length > 0) {
      return storedVersions;
    }

    return Array.from({ length: agent.version_count }, (_, i) => ({
      version_number: i + 1,
      change_description: i === 0 ? "Initial version" : "Configuration updated",
      created_at: new Date(Date.now() - (agent.version_count - i) * 86400000).toISOString(),
    }));
  };

  const handleSave = (data: Partial<AgentData>) => {
    if (editingAgentId && editingAgentId !== "new") {
      const visibleAgent = agents.find((agent) => agent.id === editingAgentId);

      if (isUsingFallbackAgents && visibleAgent) {
        dispatch(
          setAgents(
            agents.map((agent) =>
              agent.id === editingAgentId
                ? { ...agent, ...data, updated_at: new Date().toISOString() }
                : agent,
            ),
          ),
        );
      } else {
        dispatch(updateAgent({ id: editingAgentId, ...data }));
      }
    } else if (editingAgentId === "new") {
      const newAgent: AgentData = {
        id: `custom-${Date.now()}`,
        name: data.name ?? "New Agent",
        description: data.description,
        system_prompt: data.system_prompt ?? "",
        avatar_emoji: "🤖",
        permission_level: data.permission_level ?? 1,
        is_preset: false,
        is_active: true,
        tools: [],
        default_model: data.default_model ?? "deepseek-chat",
        temperature: data.temperature ?? 0.7,
        version_count: 1,
        updated_at: new Date().toISOString(),
      };
      if (isUsingFallbackAgents) {
        dispatch(setAgents([...agents, newAgent]));
      } else {
        dispatch(addAgent(newAgent));
      }
    }
    dispatch(setEditingAgent(null));
  };

  const handleDelete = (id: string) => {
    dispatch(removeAgent(id));
  };

  const handleUseTemplate = (tpl: AgentTemplate) => {
    const newAgent: AgentData = {
      id: `custom-${Date.now()}`,
      name: tpl.name,
      description: tpl.description,
      system_prompt: tpl.system_prompt,
      avatar_emoji: tpl.avatar_emoji,
      permission_level: 1,
      is_preset: false,
      is_active: true,
      tools: tpl.tools,
      default_model: "deepseek-chat",
      temperature: 0.7,
      version_count: 1,
      updated_at: new Date().toISOString(),
    };
    if (isUsingFallbackAgents) {
      dispatch(setAgents([...agents, newAgent]));
    } else {
      dispatch(addAgent(newAgent));
    }
    dispatch(setActiveTab("agents"));
  };

  const handleSaveTemplate = (data: Partial<AgentTemplate>) => {
    if (editingTemplateId && editingTemplateId !== "new") {
      if (isUsingFallbackTemplates) {
        const updated = templates.map((tpl) =>
          tpl.id === editingTemplateId ? { ...tpl, ...data } : tpl,
        );
        dispatch(setTemplates(updated as AgentTemplate[]));
      } else {
        dispatch(updateTemplate({ id: editingTemplateId, ...data }));
      }
    } else {
      const newTemplate: AgentTemplate = {
        id: `tpl-${Date.now()}`,
        name: data.name ?? "New Template",
        description: data.description ?? "",
        category: data.category ?? "通用",
        avatar_emoji: data.avatar_emoji ?? "🤖",
        system_prompt: data.system_prompt ?? "",
        tools: data.tools ?? [],
      };
      dispatch(addTemplate(newTemplate));
    }
    dispatch(setEditingTemplate(null));
  };

  const handleDeleteTemplate = (id: string) => {
    dispatch(removeTemplate(id));
  };

  return (
    <div
      className={cx(
        "h-full flex flex-col",
        isCompact ? "bg-white text-gray-900" : "bg-chat dark:bg-chat-dark",
      )}
    >
      {/* Tab Bar（含标题） */}
      <div
        className={cx(
          "flex items-center border-b bg-white",
          isCompact ? "border-gray-200 min-h-9 px-3" : "border-gray-200 px-4 dark:border-gray-700",
        )}
      >
        <span
          className={cx(
            "font-medium shrink-0 mr-3",
            isCompact ? "text-[10px] uppercase tracking-wide text-gray-400" : "text-xs",
          )}
        >
          {t("nav.agents")}
        </span>
        <div
          className="flex flex-1"
          role="tablist"
          aria-label="Agent tabs"
        >
          <button
            type="button"
            id="agent-tab-agents"
            role="tab"
            aria-selected={activeTab === "agents"}
            onClick={() => dispatch(setActiveTab("agents"))}
            className={tabButtonClass(activeTab === "agents", isCompact)}
          >
            {t("agent.tab.agents")}
          </button>
          <button
            type="button"
            id="agent-tab-templates"
            role="tab"
            aria-selected={activeTab === "templates"}
            onClick={() => dispatch(setActiveTab("templates"))}
            className={tabButtonClass(activeTab === "templates", isCompact)}
          >
            {t("agent.tab.templates")}
          </button>
        </div>
      </div>

      {/* Content */}
      <div
        className={cx("flex-1 overflow-y-auto", isCompact ? "p-2 space-y-2" : "p-4 space-y-4")}
        role="tabpanel"
        aria-labelledby={`agent-tab-${activeTab}`}
      >
        {/* ===== AGENTS TAB ===== */}
        {activeTab === "agents" && (
          <>
            {/* Search + Filter */}
            <div className="flex gap-1.5">
              <input
                value={searchQuery}
                onChange={(e) => dispatch(setSearchQuery(e.target.value))}
                placeholder={t("common.search")}
                className="flex-1 min-w-0 border rounded bg-white border-gray-200 px-2 py-1 text-[10px] text-gray-900 placeholder:text-gray-400 outline-none focus:border-blue-400"
              />
              <select
                value={statusFilter}
                onChange={(e) => dispatch(setStatusFilter(e.target.value as typeof statusFilter))}
                className="border rounded bg-white border-gray-200 px-1.5 py-1 text-[10px] text-gray-900 shrink-0"
              >
                <option value="all">All</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            {/* New Agent button */}
            <button
              type="button"
              onClick={() => dispatch(setEditingAgent("new"))}
              className="w-full text-[10px] rounded bg-blue-600 text-white hover:bg-blue-700 py-1"
            >
              + New Agent
            </button>

            {/* Agent Editor (for new or editing existing agents) */}
            {editingAgentId && (
              <AgentEditor
                agent={
                  editingAgentId !== "new"
                    ? agents.find((a) => a.id === editingAgentId)
                    : undefined
                }
                onSave={handleSave}
                onCancel={() => dispatch(setEditingAgent(null))}
              />
            )}

            {/* Agent Grid */}
            <div className={cx("grid", isCompact ? "gap-1.5" : "gap-3")}>
              {filtered.map((agent) => (
                <div key={agent.id}>
                  <AgentCard
                    agent={agent}
                    variant={variant}
                    onEdit={(id) => {
                      dispatch(setEditingAgent(id));
                      setShowVersions(null);
                    }}
                    onDelete={handleDelete}
                  />
                  <button
                    type="button"
                    onClick={() => setShowVersions(showVersions === agent.id ? null : agent.id)}
                    className="text-xs text-blue-600 hover:underline mt-1 ml-2"
                  >
                    {showVersions === agent.id ? "Hide" : "Show"} Version History
                  </button>
                  {showVersions === agent.id && (
                    <div className="ml-4 mt-2 border-l-2 pl-4">
                      <VersionHistory versions={getAgentVersions(agent)} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        {/* ===== TEMPLATES TAB ===== */}
        {activeTab === "templates" && (
          <>
            {/* Search */}
            <input
              value={templateSearchQuery}
              onChange={(e) => dispatch(setTemplateSearchQuery(e.target.value))}
              placeholder={t("common.search")}
              className="w-full border rounded bg-white border-gray-200 px-2 py-1 text-[10px] text-gray-900 placeholder:text-gray-400 outline-none focus:border-blue-400"
            />
            {/* New Template button */}
            <button
              type="button"
              onClick={() => dispatch(setEditingTemplate("new"))}
              className="w-full text-[10px] rounded bg-blue-600 text-white hover:bg-blue-700 py-1"
            >
              + New Template
            </button>

            {/* Template Editor (for new or editing existing templates) */}
            {editingTemplateId && (
              <TemplateEditor
                template={
                  editingTemplateId !== "new"
                    ? templates.find((t) => t.id === editingTemplateId)
                    : undefined
                }
                onSave={handleSaveTemplate}
                onCancel={() => dispatch(setEditingTemplate(null))}
              />
            )}

            {/* Template Grid */}
            <div className={cx("grid", isCompact ? "gap-1.5" : "gap-3")}>
              {filteredTemplates.map((tpl) => (
                <TemplateCard
                  key={tpl.id}
                  template={tpl}
                  variant={variant}
                  onUse={handleUseTemplate}
                  onEdit={(id) => dispatch(setEditingTemplate(id))}
                  onDelete={handleDeleteTemplate}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
