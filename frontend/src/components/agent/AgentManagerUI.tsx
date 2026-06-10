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
import { useState } from "react";
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
          ? "border-gray-200 p-3 text-gray-900 shadow-sm hover:shadow-md"
          : "p-4 dark:bg-gray-800 hover:shadow-md",
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex gap-3">
          <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center text-lg">
            {agent.avatar_emoji ?? "🤖"}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-medium text-sm">{agent.name}</h3>
              {agent.is_preset && (
                <span className="text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 px-1.5 py-0.5 rounded">
                  Preset
                </span>
              )}
              {!agent.is_active && (
                <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-500 px-1.5 py-0.5 rounded">
                  Inactive
                </span>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
              {agent.description ?? t("status.empty")}
            </p>
          </div>
        </div>
        <div className="flex gap-1">
          <button
            type="button"
            onClick={() => onEdit(agent.id)}
            className="text-xs px-2 py-1 rounded hover:bg-accent"
            title={t("action.edit")}
            aria-label={`${t("action.edit")} ${agent.name}`}
          >
            ✏️
          </button>
          {!agent.is_preset && (
            <button
              type="button"
              onClick={() => onDelete(agent.id)}
              className="text-xs px-2 py-1 rounded hover:bg-red-100 text-red-500"
              title={t("action.delete")}
              aria-label={`${t("action.delete")} ${agent.name}`}
            >
              🗑️
            </button>
          )}
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-1">
        {agent.tools?.map((tool: string) => (
          <span
            key={tool}
            className="text-xs bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-200 px-1.5 py-0.5 rounded"
          >
            {tool}
          </span>
        ))}
      </div>
      <div className="mt-3 flex justify-between text-xs text-muted-foreground">
        <span>Model: {agent.default_model}</span>
        <span>Level: L{agent.permission_level}</span>
        <span>v{agent.version_count}</span>
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
  const [systemPrompt, setSystemPrompt] = useState("");
  const [model, setModel] = useState(agent?.default_model ?? "deepseek-chat");
  const [level, setLevel] = useState(agent?.permission_level ?? 1);
  const [temperature, setTemperature] = useState(agent?.temperature ?? 0.7);

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
              default_model: model,
              permission_level: level,
              temperature,
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
          ? "border-gray-200 p-3 text-gray-900 shadow-sm hover:shadow-md"
          : "p-4 dark:bg-gray-800 hover:shadow-md",
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex gap-3">
          <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center text-lg">
            {template.avatar_emoji}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-medium text-sm">{template.name}</h3>
              <span className="text-xs bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-200 px-1.5 py-0.5 rounded">
                {template.category}
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
              {template.description}
            </p>
          </div>
        </div>
        <div className="flex gap-1">
          <button
            type="button"
            onClick={() => onEdit(template.id)}
            className="text-xs px-2 py-1 rounded hover:bg-accent"
            title={t("action.edit")}
            aria-label={`${t("action.edit")} ${template.name}`}
          >
            ✏️
          </button>
          <button
            type="button"
            onClick={() => onDelete(template.id)}
            className="text-xs px-2 py-1 rounded hover:bg-red-100 text-red-500"
            title={t("action.delete")}
            aria-label={`${t("action.delete")} ${template.name}`}
          >
            🗑️
          </button>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-1">
        {template.tools.map((tool: string) => (
          <span
            key={tool}
            className="text-xs bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-200 px-1.5 py-0.5 rounded"
          >
            {tool}
          </span>
        ))}
      </div>
      <div className="mt-3 flex justify-between items-center">
        <span className="text-xs text-muted-foreground line-clamp-2 flex-1">
          {template.system_prompt}
        </span>
        <button
          type="button"
          onClick={() => onUse(template)}
          className="ml-2 text-xs px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 shrink-0"
        >
          Use
        </button>
      </div>
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
    permission_level: 4,
    is_preset: true,
    is_active: true,
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
    system_prompt: "You are a market analyst.",
    tools: ["web_search", "file_read", "code_execution"],
  },
  {
    id: "tp2",
    name: "代码审查",
    description: "审查代码质量、安全漏洞、性能优化",
    category: "开发",
    avatar_emoji: "🔍",
    system_prompt: "You are a code reviewer.",
    tools: ["code_execution", "file_read"],
  },
  {
    id: "tp3",
    name: "文档撰写",
    description: "撰写技术文档、报告、方案",
    category: "内容",
    avatar_emoji: "✍️",
    system_prompt: "You are a technical writer.",
    tools: ["file_read", "file_write"],
  },
  {
    id: "tp4",
    name: "数据分析",
    description: "SQL查询、数据清洗、统计分析、图表生成",
    category: "分析",
    avatar_emoji: "📊",
    system_prompt: "You are a data analyst.",
    tools: ["database_query", "code_execution", "file_read"],
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
      {/* Header */}
      <div
        className={cx(
          "border-b flex items-center justify-between",
          isCompact
            ? "min-h-11 border-gray-200 bg-white px-3 py-2"
            : "h-12 bg-white px-4 dark:bg-gray-900",
        )}
      >
        <h2
          className={cx(
            "font-medium",
            isCompact ? "text-xs uppercase tracking-wide text-gray-500" : "text-sm",
          )}
        >
          {t("nav.agents")}
        </h2>
      </div>

      {/* Tab Bar */}
      <div
        className={cx(
          "flex border-b bg-white",
          isCompact ? "border-gray-200" : "border-gray-200 dark:border-gray-700",
        )}
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

      {/* Content */}
      <div
        className={cx("flex-1 overflow-y-auto space-y-4", isCompact ? "p-3" : "p-4")}
        role="tabpanel"
        aria-labelledby={`agent-tab-${activeTab}`}
      >
        {/* ===== AGENTS TAB ===== */}
        {activeTab === "agents" && (
          <>
            {/* Search, Filter + New Agent button */}
            <div className={cx("flex gap-2", isCompact && "items-center")}>
              <input
                value={searchQuery}
                onChange={(e) => dispatch(setSearchQuery(e.target.value))}
                placeholder={t("common.search")}
                className={cx(
                  "flex-1 border rounded-lg bg-white",
                  isCompact
                    ? "border-gray-200 px-2.5 py-1.5 text-xs text-gray-900 placeholder:text-gray-400"
                    : "px-3 py-1.5 text-sm dark:bg-gray-800",
                )}
              />
              <select
                value={statusFilter}
                onChange={(e) => dispatch(setStatusFilter(e.target.value as typeof statusFilter))}
                className={cx(
                  "border rounded-lg bg-white",
                  isCompact
                    ? "border-gray-200 px-2 py-1.5 text-xs text-gray-900"
                    : "px-3 py-1.5 text-sm dark:bg-gray-800",
                )}
              >
                <option value="all">All</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
              <button
                type="button"
                onClick={() => dispatch(setEditingAgent("new"))}
                className={cx(
                  "text-xs rounded bg-blue-600 text-white hover:bg-blue-700",
                  isCompact ? "px-2.5 py-1.5 shadow-sm" : "px-3 py-1",
                )}
              >
                + New Agent
              </button>
            </div>

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
            <div className={cx("grid", isCompact ? "gap-2" : "gap-3")}>
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
            {/* Search + New Template button */}
            <div className={cx("flex gap-2", isCompact && "items-center")}>
              <input
                value={templateSearchQuery}
                onChange={(e) => dispatch(setTemplateSearchQuery(e.target.value))}
                placeholder={t("common.search")}
                className={cx(
                  "flex-1 border rounded-lg bg-white",
                  isCompact
                    ? "border-gray-200 px-2.5 py-1.5 text-xs text-gray-900 placeholder:text-gray-400"
                    : "px-3 py-1.5 text-sm dark:bg-gray-800",
                )}
              />
              <button
                type="button"
                onClick={() => dispatch(setEditingTemplate("new"))}
                className={cx(
                  "text-xs rounded bg-blue-600 text-white hover:bg-blue-700",
                  isCompact ? "px-2.5 py-1.5 shadow-sm" : "px-3 py-1",
                )}
              >
                + New Template
              </button>
            </div>

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
            <div className={cx("grid", isCompact ? "gap-2" : "gap-3")}>
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
