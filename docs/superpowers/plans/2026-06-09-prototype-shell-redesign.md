# Prototype Shell Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the React frontend shell to match `doc/web.html`: blue title bar, 24/60/16 three-column workspace, embedded conversation/assets/performance/security/Agent panels, and bottom status bar.

**Architecture:** Convert `LayoutShell` from route/sidebar navigation into a fixed workspace shell that owns the top bar, left tabs, center conversation surface, right tabs, and footer. Refactor existing module components to support light compact rendering inside the shell while preserving Redux behavior and compatibility routes.

**Tech Stack:** React 18, TypeScript, Redux Toolkit, React Router v6, Tailwind CSS, lucide-react, Vitest, Testing Library.

---

## Scope and Constraints

- The approved design lives at `docs/superpowers/specs/2026-06-09-prototype-shell-redesign-design.md`.
- Match the light prototype in `doc/web.html` first.
- Keep user-facing strings in `frontend/src/i18n.ts` and access them via `t()`.
- Do not add Font Awesome or other CDN dependencies. Use `lucide-react`.
- This workspace is not currently a git repository. The checkpoint steps below include `git status` checks and explicit instructions to skip commits when Git is unavailable.

## File Structure

Modify these files:

- `frontend/src/i18n.ts` — add prototype shell labels, status text, section labels, and action labels.
- `frontend/src/components/layout/LayoutShell.tsx` — replace old dark nav shell with the prototype workspace shell and route-to-tab activation.
- `frontend/src/components/conversation/ConversationUI.tsx` — export reusable `ConversationSidebar`, `ConversationWorkspace`, and `ChatInput`-style pieces; restyle them to the light prototype.
- `frontend/src/components/asset/AssetPanel.tsx` — add compact light rendering for the left `资产` tab.
- `frontend/src/components/monitor/MonitorPanel.tsx` — add controlled light rendering for right `性能` and `安全` tabs.
- `frontend/src/components/agent/AgentManagerUI.tsx` — add compact light rendering for right `Agent` tab.
- `frontend/src/__tests__/components/layout/LayoutShell.test.tsx` — replace old navigation assertions with prototype shell assertions.
- `frontend/src/__tests__/components/conversation/ConversationUI.test.tsx` — update for Chinese section labels and prototype input.
- `frontend/src/__tests__/components/asset/AssetPanel.test.tsx` — verify compact/light asset rendering still filters and previews.
- `frontend/src/__tests__/components/monitor/MonitorPanel.test.tsx` — verify right-panel performance/security labels and tab switching.
- `frontend/src/__tests__/components/agent/AgentManagerUI.test.tsx` — verify compact Agent mode still lists agents and supports editor/template actions.

Do not create new app-level state slices. Local tab state in `LayoutShell` is enough for this pass.

---

## Task 1: Add i18n keys and failing shell tests

**Files:**
- Modify: `frontend/src/i18n.ts`
- Modify: `frontend/src/__tests__/components/layout/LayoutShell.test.tsx`

- [ ] **Step 1: Add the prototype shell translation keys**

Update `frontend/src/i18n.ts` by adding these entries inside the `translations` object:

```ts
    // Prototype shell
    "shell.product": "DeepSeek",
    "shell.version": "V6.2.0",
    "shell.workspace": "NEXUS AI",
    "shell.newConversation": "新建对话",
    "shell.pinnedSpace": "置顶空间",
    "shell.activeConversations": "活跃会话",
    "shell.performance": "性能",
    "shell.security": "安全",
    "shell.agent": "Agent",
    "shell.hardwareMonitor": "硬件监控",
    "shell.recentActivity": "近期活动",
    "shell.gpuMemory": "GPU显存",
    "shell.systemMemory": "系统内存",
    "shell.statusApi": "DeepSeek API | API Key已配置",
    "shell.exportLogs": "导出日志",
    "shell.ping": "PING 15ms",
    "shell.inputPlaceholder": "输入您的问题...",
    "shell.viewBackup": "查看备份",
    "shell.mergeData": "合并数据",
    "shell.saveTemplate": "存为模板",
    "shell.taskComplete": "任务执行完毕。监控代码已部署。财务数据已更新并备份，请确认。",
    "shell.deployMonitorCode": "部署监控代码(100%)",
    "shell.codeFilename": "spider_probe_server.py",
    "shell.productOps": "产品运营",
    "shell.projectDev": "项目开发",
    "shell.competitorAnalysis": "竞品销量异动分析",
    "shell.financeProcessing": "年度财报数据处理",
    "shell.preferenceAlignment": "用户偏好特征对齐",
```

- [ ] **Step 2: Replace the layout shell tests with prototype expectations**

Replace the full contents of `frontend/src/__tests__/components/layout/LayoutShell.test.tsx` with:

```tsx
import { describe, it, expect } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@/__tests__/test-utils";
import { LayoutShell } from "@/components/layout/LayoutShell";

describe("LayoutShell", () => {
  it("renders the prototype title bar", () => {
    renderWithProviders(<LayoutShell />);

    expect(screen.getByText("DeepSeek")).toBeInTheDocument();
    expect(screen.getByText("V6.2.0")).toBeInTheDocument();
    expect(screen.getByText("NEXUS AI")).toBeInTheDocument();
  });

  it("renders left workspace tabs", () => {
    renderWithProviders(<LayoutShell />);

    expect(screen.getByRole("button", { name: "会话" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "资产" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /新建对话/ })).toBeInTheDocument();
  });

  it("switches the left panel to assets", () => {
    renderWithProviders(<LayoutShell />);

    fireEvent.click(screen.getByRole("button", { name: "资产" }));

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

    expect(screen.getByRole("button", { name: "性能" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "安全" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Agent" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Agent" }));

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

    expect(screen.getByText("sales_report.csv")).toBeInTheDocument();
  });

  it("activates agent tab from /agents route", () => {
    renderWithProviders(<LayoutShell />, { initialRoute: "/agents" });

    expect(screen.getByText("数字主管")).toBeInTheDocument();
    expect(screen.getByText("风控顾问")).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Run the shell test and verify it fails for the current implementation**

Run:

```bash
cd frontend && npm run test -- src/__tests__/components/layout/LayoutShell.test.tsx
```

Expected result before implementation: FAIL. The failure should mention missing prototype text such as `DeepSeek`, `新建对话`, `性能`, or `输入您的问题...`.

- [ ] **Step 4: Checkpoint**

Run:

```bash
git status
```

Expected in this workspace: `fatal: not a git repository`. If so, do not commit. If a future worker runs this inside a Git repository, commit with:

```bash
git add frontend/src/i18n.ts frontend/src/__tests__/components/layout/LayoutShell.test.tsx
git commit -m "test: define prototype shell expectations"
```

---

## Task 2: Refactor conversation UI into reusable prototype workspace pieces

**Files:**
- Modify: `frontend/src/components/conversation/ConversationUI.tsx`
- Modify: `frontend/src/__tests__/components/conversation/ConversationUI.test.tsx`

- [ ] **Step 1: Replace conversation tests with prototype-compatible expectations**

Replace the full contents of `frontend/src/__tests__/components/conversation/ConversationUI.test.tsx` with:

```tsx
import { describe, it, expect } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@/__tests__/test-utils";
import {
  ConversationUI,
  ConversationSidebar,
  ConversationWorkspace,
} from "@/components/conversation/ConversationUI";

describe("ConversationUI", () => {
  it("renders the full conversation workspace", () => {
    renderWithProviders(<ConversationUI />);

    expect(screen.getByText("置顶空间")).toBeInTheDocument();
    expect(screen.getByText("活跃会话")).toBeInTheDocument();
    expect(screen.getByText(/建议：建议主攻/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText("输入您的问题...")).toBeInTheDocument();
  });

  it("renders conversation sidebar with new conversation button", () => {
    renderWithProviders(<ConversationSidebar />);

    expect(screen.getByRole("button", { name: /新建对话/ })).toBeInTheDocument();
    expect(screen.getByText("置顶空间")).toBeInTheDocument();
    expect(screen.getByText("数据分析任务示例")).toBeInTheDocument();
    expect(screen.getByText("代码审查讨论")).toBeInTheDocument();
  });

  it("clicking new conversation creates one in store", () => {
    const { store } = renderWithProviders(<ConversationSidebar />);

    fireEvent.click(screen.getByRole("button", { name: /新建对话/ }));

    const state = store.getState() as unknown as {
      conversation: { conversations: Array<{ title: string }> };
    };
    expect(state.conversation.conversations.length).toBeGreaterThanOrEqual(1);
  });

  it("renders prototype task card and action buttons", () => {
    renderWithProviders(<ConversationWorkspace />);

    expect(screen.getByText("部署监控代码(100%)")).toBeInTheDocument();
    expect(screen.getByText("spider_probe_server.py")).toBeInTheDocument();
    expect(screen.getByText(/任务执行完毕/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "查看备份" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "合并数据" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "存为模板" })).toBeInTheDocument();
  });

  it("clears input after typing and clicking send", () => {
    renderWithProviders(<ConversationWorkspace />);

    const input = screen.getByPlaceholderText("输入您的问题...") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "Hello world" } });
    expect(input.value).toBe("Hello world");

    fireEvent.click(screen.getByRole("button", { name: "发送" }));
    expect(input.value).toBe("");
  });
});
```

- [ ] **Step 2: Run the conversation test and verify it fails before refactor**

Run:

```bash
cd frontend && npm run test -- src/__tests__/components/conversation/ConversationUI.test.tsx
```

Expected result before implementation: FAIL because `ConversationSidebar` and `ConversationWorkspace` are not exported and the prototype labels are missing.

- [ ] **Step 3: Replace `ConversationUI.tsx` with reusable prototype components**

Replace the full contents of `frontend/src/components/conversation/ConversationUI.tsx` with:

```tsx
/** Conversation UI - prototype workspace conversation list, task card, and input. */

import { useState, type KeyboardEvent } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Archive,
  ArrowRight,
  ChevronDown,
  Code2,
  Copy,
  FileImage,
  Folder,
  MessageCircle,
  Mic,
  Paperclip,
  PlayCircle,
  Plus,
  Radio,
  Terminal,
  CheckCircle2,
} from "lucide-react";
import type { RootState, AppDispatch } from "@/store";
import {
  addConversation,
  setActiveConversation,
  addMessage,
  type Conversation,
  type Message,
} from "@/features/conversation/conversationSlice";
import { t } from "@/i18n";

const MOCK_CONVERSATIONS: Conversation[] = [
  {
    id: "1",
    title: "数据分析任务示例",
    status: "active",
    is_pinned: true,
    message_count: 12,
    updated_at: new Date().toISOString(),
  },
  {
    id: "2",
    title: "代码审查讨论",
    status: "active",
    is_pinned: false,
    message_count: 5,
    updated_at: new Date().toISOString(),
  },
  {
    id: "3",
    title: t("shell.financeProcessing"),
    status: "active",
    is_pinned: false,
    message_count: 8,
    updated_at: new Date().toISOString(),
  },
  {
    id: "4",
    title: t("shell.preferenceAlignment"),
    status: "active",
    is_pinned: false,
    message_count: 6,
    updated_at: new Date().toISOString(),
  },
];

function useConversationData() {
  const dispatch = useDispatch<AppDispatch>();
  const { conversations: conversationsFromStore, activeConversationId, messages } = useSelector(
    (state: RootState) => state.conversation,
  );

  const conversations = conversationsFromStore.length > 0 ? conversationsFromStore : MOCK_CONVERSATIONS;
  const activeConvId = activeConversationId ?? conversations[0]?.id ?? "1";
  const activeConv = conversations.find((c) => c.id === activeConvId) ?? conversations[0];
  const activeMessages = messages[activeConvId] ?? [];

  const handleNew = () => {
    const newConv: Conversation = {
      id: `conv-${Date.now()}`,
      title: "New Conversation",
      status: "active",
      is_pinned: false,
      message_count: 0,
      updated_at: new Date().toISOString(),
    };
    dispatch(addConversation(newConv));
    dispatch(setActiveConversation(newConv.id));
  };

  const handleSend = (content: string) => {
    dispatch(
      addMessage({
        conversationId: activeConvId,
        message: {
          id: `msg-${Date.now()}`,
          role: "user",
          content,
          created_at: new Date().toISOString(),
        },
      }),
    );
  };

  return {
    conversations,
    activeConvId,
    activeConv,
    activeMessages,
    onSelect: (id: string) => dispatch(setActiveConversation(id)),
    onNew: handleNew,
    onSend: handleSend,
  };
}

function ConversationItem({
  conv,
  active,
  onSelect,
}: {
  conv: Conversation;
  active: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(conv.id)}
      className={`my-1.5 w-full rounded px-2 py-3 text-left text-sm transition-colors ${
        active ? "border-l-2 border-blue-600 bg-blue-50 text-gray-900" : "hover:bg-[#f7f8fa]"
      }`}
    >
      <div className="flex items-center gap-2">
        <MessageCircle size={16} className={active ? "text-blue-600" : "text-gray-400"} />
        <span className="truncate">{conv.title || "Untitled"}</span>
      </div>
      <div className="ml-6 mt-1 truncate text-xs text-gray-400">
        {active ? "自动分析已启动..." : `${conv.message_count} messages`}
      </div>
    </button>
  );
}

export function ConversationSidebar() {
  const { conversations, activeConvId, onSelect, onNew } = useConversationData();
  const pinned = conversations.filter((c) => c.is_pinned);
  const unpinned = conversations.filter((c) => !c.is_pinned);

  return (
    <div className="flex h-full flex-col bg-white text-gray-900">
      <div className="p-4 pt-5">
        <button
          type="button"
          onClick={onNew}
          className="flex w-full items-center justify-center gap-1 rounded bg-blue-600 py-2 text-sm text-white hover:bg-blue-700"
        >
          <Plus size={15} />
          {t("shell.newConversation")}
        </button>
      </div>

      <div className="flex-1 overflow-auto px-4 pb-4 pt-2">
        <div className="mb-2 mt-4 text-xs text-gray-400">{t("shell.pinnedSpace")}</div>
        <div className="rounded px-2 py-2.5 hover:bg-[#f7f8fa]">
          <div className="flex items-center gap-2 text-sm">
            <Folder size={16} className="text-gray-500" />
            {t("shell.productOps")}
            <Archive size={14} className="ml-auto text-gray-300" />
          </div>
        </div>
        <div className="rounded px-2 py-2.5 hover:bg-[#f7f8fa]">
          <div className="flex items-center gap-2 text-sm">
            <Code2 size={16} className="text-gray-500" />
            {t("shell.projectDev")}
            <Archive size={14} className="ml-auto text-gray-300" />
          </div>
        </div>

        {pinned.map((conv) => (
          <ConversationItem key={conv.id} conv={conv} active={conv.id === activeConvId} onSelect={onSelect} />
        ))}

        <div className="mb-2 mt-5 text-xs text-gray-400">{t("shell.activeConversations")}</div>
        {unpinned.map((conv) => (
          <ConversationItem key={conv.id} conv={conv} active={conv.id === activeConvId} onSelect={onSelect} />
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";

  return (
    <div className={`flex gap-3 px-4 py-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-200 text-sm">
        {isUser ? "👤" : msg.agent_emoji ?? "🤖"}
      </div>
      <div className={`max-w-[75%] ${isUser ? "text-right" : "text-left"}`}>
        {msg.agent_name && <div className="mb-1 text-xs text-gray-500">{msg.agent_name}</div>}
        <div className={`rounded-lg px-4 py-2 text-sm ${isUser ? "bg-blue-600 text-white" : "bg-[#f7f8fa]"}`}>
          {msg.content ? <div className="whitespace-pre-wrap break-words">{msg.content}</div> : <div className="italic text-gray-400">...</div>}
        </div>
      </div>
    </div>
  );
}

function PrototypeTaskCard() {
  return (
    <div className="rounded-lg bg-[#f7f8fa] p-4">
      <p className="text-sm leading-6 text-gray-800">
        建议：建议主攻 899元以上“长续航+骨传导”细分市场，避开低价竞争。
        <br />
        此外，我已在沙盒环境中为您生成并运行了数据监控代码，请查看：
      </p>

      <div className="mt-4 flex items-center gap-2 text-sm">
        <span>{t("shell.deployMonitorCode")}</span>
        <ChevronDown size={16} className="text-gray-500" />
      </div>

      <div className="mt-3 flex items-center rounded bg-gray-800 p-2.5 text-sm text-white">
        <span className="font-mono">_&gt; {t("shell.codeFilename")}</span>
        <span className="ml-3 rounded bg-gray-600 px-1.5 text-xs">python</span>
        <div className="ml-auto flex gap-3">
          <Copy size={15} />
          <PlayCircle size={16} />
        </div>
      </div>

      <div className="mt-4 rounded border border-emerald-300 bg-green-50 p-4">
        <div className="flex items-center gap-1 text-sm text-emerald-600">
          <CheckCircle2 size={16} />
          {t("shell.taskComplete")}
        </div>
        <div className="mt-4 flex gap-3">
          <button type="button" className="rounded border border-gray-300 px-3 py-1.5 text-sm">
            {t("shell.viewBackup")}
          </button>
          <button type="button" className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white">
            {t("shell.mergeData")}
          </button>
          <button type="button" className="rounded border border-gray-300 px-3 py-1.5 text-sm">
            {t("shell.saveTemplate")}
          </button>
        </div>
      </div>
    </div>
  );
}

function ChatInput({ onSend }: { onSend: (content: string) => void }) {
  const [value, setValue] = useState("");

  const handleSend = () => {
    const trimmed = value.trim();
    if (trimmed) {
      onSend(trimmed);
      setValue("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-200 p-4">
      <div className="mb-3 flex items-center gap-3 text-gray-500">
        <Paperclip size={17} />
        <FileImage size={17} />
        <Mic size={17} />
        <Radio size={17} />
        <Terminal size={17} />
      </div>
      <div className="flex gap-3">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t("shell.inputPlaceholder")}
          className="flex-1 rounded border px-3 py-2.5 text-sm outline-none focus:border-blue-600"
        />
        <button
          type="button"
          aria-label={t("action.send")}
          onClick={handleSend}
          disabled={!value.trim()}
          className="rounded bg-blue-600 px-5 text-white disabled:opacity-50"
        >
          <ArrowRight size={17} />
        </button>
      </div>
    </div>
  );
}

export function ConversationWorkspace() {
  const { activeMessages, onSend } = useConversationData();

  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex-1 overflow-auto p-5">
        <PrototypeTaskCard />
        {activeMessages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}
      </div>
      <ChatInput onSend={onSend} />
    </div>
  );
}

export function ConversationUI() {
  return (
    <div className="flex h-full bg-white">
      <div className="hidden w-[24%] min-w-64 shrink-0 border-r border-gray-200 md:block">
        <ConversationSidebar />
      </div>
      <div className="min-w-0 flex-1">
        <ConversationWorkspace />
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run conversation tests and verify they pass**

Run:

```bash
cd frontend && npm run test -- src/__tests__/components/conversation/ConversationUI.test.tsx
```

Expected result: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
git status
```

Expected in this workspace: `fatal: not a git repository`. If Git is available in a future workspace, commit with:

```bash
git add frontend/src/components/conversation/ConversationUI.tsx frontend/src/__tests__/components/conversation/ConversationUI.test.tsx
git commit -m "feat: refactor conversation into prototype workspace"
```

---

## Task 3: Make AssetPanel support compact light rendering

**Files:**
- Modify: `frontend/src/components/asset/AssetPanel.tsx`
- Modify: `frontend/src/__tests__/components/asset/AssetPanel.test.tsx`

- [ ] **Step 1: Replace asset tests with compact-mode coverage**

Replace the full contents of `frontend/src/__tests__/components/asset/AssetPanel.test.tsx` with:

```tsx
import { describe, it, expect } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@/__tests__/test-utils";
import { AssetPanel } from "@/components/asset/AssetPanel";

describe("AssetPanel", () => {
  it("renders compact light asset list with file names", () => {
    renderWithProviders(<AssetPanel variant="compact" />);

    expect(screen.getByText("sales_report.csv")).toBeInTheDocument();
    expect(screen.getByText("architecture.png")).toBeInTheDocument();
    expect(screen.getByText("readme.md")).toBeInTheDocument();
  });

  it("search filters files case-insensitively", () => {
    renderWithProviders(<AssetPanel variant="compact" />);

    fireEvent.change(screen.getByPlaceholderText("搜索..."), { target: { value: "csv" } });

    expect(screen.getByText("sales_report.csv")).toBeInTheDocument();
    expect(screen.queryByText("architecture.png")).not.toBeInTheDocument();
    expect(screen.queryByText("readme.md")).not.toBeInTheDocument();
  });

  it("clicking asset shows preview panel", () => {
    renderWithProviders(<AssetPanel variant="compact" />);

    fireEvent.click(screen.getByText("architecture.png"));

    expect(screen.getByText("Type: image")).toBeInTheDocument();
    expect(screen.getByText("MIME: image/png")).toBeInTheDocument();
  });

  it("clicking same asset again hides preview", () => {
    renderWithProviders(<AssetPanel variant="compact" />);

    fireEvent.click(screen.getByText("architecture.png"));
    expect(screen.getByText("Type: image")).toBeInTheDocument();

    fireEvent.click(screen.getAllByText("architecture.png")[0]);
    expect(screen.queryByText("Type: image")).not.toBeInTheDocument();
  });

  it("shows empty state when no assets match search", () => {
    renderWithProviders(<AssetPanel variant="compact" />);

    fireEvent.change(screen.getByPlaceholderText("搜索..."), { target: { value: "nonexistent_file_xyz" } });

    expect(screen.getByText("暂无数据")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run asset test and verify it fails before implementation**

Run:

```bash
cd frontend && npm run test -- src/__tests__/components/asset/AssetPanel.test.tsx
```

Expected result before implementation: FAIL because `variant` is not a supported prop.

- [ ] **Step 3: Replace `AssetPanel.tsx` with compact light support**

Replace the full contents of `frontend/src/components/asset/AssetPanel.tsx` with:

```tsx
/** Asset Panel UI - file browsing, search, preview. */

import { useDispatch, useSelector } from "react-redux";
import type { RootState, AppDispatch } from "@/store";
import { setSelectedAsset, setSearchQuery, type AssetItem } from "@/features/asset/assetSlice";
import { t } from "@/i18n";

interface AssetPanelProps {
  variant?: "full" | "compact";
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getAssetIcon(previewType: string): string {
  switch (previewType) {
    case "image": return "🖼️";
    case "pdf": return "📕";
    case "table": return "📊";
    case "text": return "📄";
    default: return "📎";
  }
}

const MOCK_ASSETS: AssetItem[] = [
  { id: "a1", filename: "sales_report.csv", original_filename: "sales_report.csv", file_size: 245760, mime_type: "text/csv", preview_type: "table", created_at: new Date().toISOString() },
  { id: "a2", filename: "architecture.png", original_filename: "architecture.png", file_size: 1048576, mime_type: "image/png", preview_type: "image", created_at: new Date().toISOString() },
  { id: "a3", filename: "readme.md", original_filename: "readme.md", file_size: 4096, mime_type: "text/markdown", preview_type: "text", created_at: new Date().toISOString() },
];

export function AssetPanel({ variant = "full" }: AssetPanelProps) {
  const dispatch = useDispatch<AppDispatch>();
  const { selectedAssetId, searchQuery } = useSelector((state: RootState) => state.asset);
  const assets = MOCK_ASSETS;
  const filtered = assets.filter((a) => !searchQuery || a.original_filename.toLowerCase().includes(searchQuery.toLowerCase()));
  const selected = assets.find((a) => a.id === selectedAssetId);

  const rootClass = variant === "compact"
    ? "flex h-full flex-col bg-white text-gray-900"
    : "flex h-full flex-col bg-white text-gray-900";

  return (
    <div className={rootClass}>
      <div className="border-b border-gray-200 p-3">
        {variant === "full" && <h2 className="text-sm font-medium">{t("nav.assets")}</h2>}
        <input
          value={searchQuery}
          onChange={(e) => dispatch(setSearchQuery(e.target.value))}
          placeholder={t("common.search")}
          className="mt-2 w-full rounded border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-900 outline-none focus:border-blue-600"
        />
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {filtered.map((asset) => (
          <button
            type="button"
            key={asset.id}
            onClick={() => dispatch(setSelectedAsset(asset.id === selectedAssetId ? null : asset.id))}
            className={`flex w-full items-center gap-2 rounded px-2 py-2 text-left text-xs transition-colors ${
              asset.id === selectedAssetId ? "bg-blue-50 text-blue-700" : "hover:bg-[#f7f8fa]"
            }`}
          >
            <span>{getAssetIcon(asset.preview_type)}</span>
            <span className="min-w-0 flex-1 truncate">{asset.original_filename}</span>
            <span className="text-gray-400">{formatSize(asset.file_size)}</span>
          </button>
        ))}

        {filtered.length === 0 && <div className="py-8 text-center text-xs text-gray-400">{t("status.empty")}</div>}
      </div>

      {selected && (
        <div className="border-t border-gray-200 p-3">
          <h3 className="mb-2 truncate text-xs font-medium">{selected.original_filename}</h3>
          <div className="space-y-1 rounded bg-[#f7f8fa] p-2 text-xs text-gray-600">
            <div>Type: {selected.preview_type}</div>
            <div>Size: {formatSize(selected.file_size)}</div>
            <div>MIME: {selected.mime_type ?? "unknown"}</div>
            <div className="mt-2 flex h-24 items-center justify-center rounded bg-white text-2xl">
              {getAssetIcon(selected.preview_type)}
            </div>
          </div>
          <div className="mt-2 flex gap-1">
            <button type="button" className="flex-1 rounded bg-blue-600 py-1 text-xs text-white" title={t("action.download")}>
              ⬇ Download
            </button>
            <button type="button" className="rounded border border-red-200 px-2 py-1 text-xs text-red-500" title={t("action.delete")}>
              🗑️
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run asset tests and verify they pass**

Run:

```bash
cd frontend && npm run test -- src/__tests__/components/asset/AssetPanel.test.tsx
```

Expected result: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
git status
```

Expected in this workspace: `fatal: not a git repository`. If Git is available in a future workspace, commit with:

```bash
git add frontend/src/components/asset/AssetPanel.tsx frontend/src/__tests__/components/asset/AssetPanel.test.tsx
git commit -m "feat: add compact light asset panel"
```

---

## Task 4: Make MonitorPanel support controlled right-panel tabs

**Files:**
- Modify: `frontend/src/components/monitor/MonitorPanel.tsx`
- Modify: `frontend/src/__tests__/components/monitor/MonitorPanel.test.tsx`

- [ ] **Step 1: Replace monitor tests with light right-panel expectations**

Replace the full contents of `frontend/src/__tests__/components/monitor/MonitorPanel.test.tsx` with:

```tsx
import { describe, it, expect } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@/__tests__/test-utils";
import { MonitorPanel } from "@/components/monitor/MonitorPanel";

describe("MonitorPanel", () => {
  it("renders performance content by default", () => {
    renderWithProviders(<MonitorPanel variant="compact" />);

    expect(screen.getByText("硬件监控")).toBeInTheDocument();
    expect(screen.getByText("GPU显存")).toBeInTheDocument();
    expect(screen.getByText("系统内存")).toBeInTheDocument();
  });

  it("renders recent agent activity", () => {
    renderWithProviders(<MonitorPanel variant="compact" />);

    expect(screen.getByText("近期活动")).toBeInTheDocument();
    expect(screen.getByText("数字主管")).toBeInTheDocument();
    expect(screen.getByText("风控顾问")).toBeInTheDocument();
    expect(screen.getByText("数据专家")).toBeInTheDocument();
  });

  it("switches to security tab when uncontrolled", () => {
    renderWithProviders(<MonitorPanel variant="compact" />);

    fireEvent.click(screen.getByRole("button", { name: "安全" }));

    expect(screen.getByText("Rate Limits")).toBeInTheDocument();
    expect(screen.getByText("API Requests")).toBeInTheDocument();
    expect(screen.getByText("Recent Audit Events")).toBeInTheDocument();
  });

  it("renders controlled security content without internal tabs", () => {
    renderWithProviders(<MonitorPanel variant="compact" activeTab="security" hideTabs />);

    expect(screen.getByText("Rate Limits")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "性能" })).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run monitor test and verify it fails before implementation**

Run:

```bash
cd frontend && npm run test -- src/__tests__/components/monitor/MonitorPanel.test.tsx
```

Expected result before implementation: FAIL because `variant`, `activeTab`, and `hideTabs` are not supported.

- [ ] **Step 3: Replace `MonitorPanel.tsx` with controlled compact support**

Replace the full contents of `frontend/src/components/monitor/MonitorPanel.tsx` with:

```tsx
/** Monitor Panel - performance/security tabs, hardware bars, and agent activity. */

import { useDispatch, useSelector } from "react-redux";
import type { RootState, AppDispatch } from "@/store";
import { setActiveTab, type HardwareStats, type AgentActivity } from "@/features/monitor/monitorSlice";
import { t } from "@/i18n";

type Tab = "performance" | "security";

interface MonitorPanelProps {
  variant?: "full" | "compact";
  activeTab?: Tab;
  hideTabs?: boolean;
}

const MOCK_HARDWARE: HardwareStats = {
  cpu_percent: 25.5,
  memory_used_mb: 14200,
  memory_total_mb: 32000,
  gpu_name: "GPU显存",
  gpu_utilization_percent: 52,
};

const MOCK_ACTIVITIES: AgentActivity[] = [
  { agent_id: "1", agent_name: "数字主管", agent_emoji: "🎯", status: "working", message: "正在拆解并生成任务..." },
  { agent_id: "2", agent_name: "风控顾问", agent_emoji: "🛡️", status: "idle", message: "已拦截一次未授权访问" },
  { agent_id: "3", agent_name: "数据专家", agent_emoji: "📊", status: "idle", message: "知识库检索已完成" },
];

function ProgressBar({ label, value, detail }: { label: string; value: number; detail: string }) {
  return (
    <div className="mb-4">
      <div className="mb-1.5 flex justify-between text-xs">
        <span>{label}</span>
        <span>{detail}</span>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full bg-gray-200">
        <div className="h-full rounded-full bg-blue-600" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function PerformanceContent({ hardware, activities }: { hardware: HardwareStats; activities: AgentActivity[] }) {
  const memoryPercent = Math.round((hardware.memory_used_mb / hardware.memory_total_mb) * 100);

  return (
    <>
      <div className="mb-3 text-sm font-medium">{t("shell.hardwareMonitor")}</div>
      <ProgressBar label={t("shell.gpuMemory")} value={hardware.gpu_utilization_percent ?? 0} detail="8.4 / 16G" />
      <ProgressBar label={t("shell.systemMemory")} value={memoryPercent} detail="14.2 / 32G" />

      <div className="mb-3 mt-2 text-sm font-medium">{t("shell.recentActivity")}</div>
      <div className="space-y-5">
        {activities.map((act, index) => (
          <div key={act.agent_id} className="flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-300 text-sm">
              {act.agent_emoji}
            </div>
            <div className="min-w-0">
              <div className="text-xs">
                {act.agent_name} <span className="text-gray-400">{index === 0 ? "刚刚" : `${index}分钟前`}</span>
              </div>
              {act.message && <div className="mt-0.5 text-xs text-gray-500">{act.message}</div>}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

function SecurityContent({ rateLimits }: { rateLimits: RootState["monitor"]["rateLimits"] }) {
  return (
    <div className="space-y-4 text-xs">
      <div>
        <h3 className="mb-2 text-sm font-medium">Rate Limits</h3>
        <div className="space-y-1 rounded bg-[#f7f8fa] p-2">
          <div className="flex justify-between">
            <span>API Requests</span>
            <span className="text-emerald-600">{rateLimits.api_requests_per_min}/min</span>
          </div>
          <div className="flex justify-between">
            <span>LLM Requests</span>
            <span className="text-emerald-600">{rateLimits.llm_requests_per_min}/min</span>
          </div>
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-medium">Recent Audit Events</h3>
        <div className="space-y-1 rounded bg-[#f7f8fa] p-2 text-[10px] text-gray-500">
          <div>12:30 - agent.execute_code (数字主管)</div>
          <div>12:28 - conversation.create (user-1)</div>
          <div>12:25 - file.upload (user-1)</div>
          <div>12:20 - agent.create (admin)</div>
          <div>12:15 - conversation.archive (user-1)</div>
        </div>
      </div>
    </div>
  );
}

export function MonitorPanel({ variant = "full", activeTab: controlledTab, hideTabs = false }: MonitorPanelProps) {
  const dispatch = useDispatch<AppDispatch>();
  const { activeTab: storeTab, hardware: hardwareFromStore, agentActivities: activitiesFromStore, rateLimits } = useSelector(
    (state: RootState) => state.monitor,
  );
  const activeTab = controlledTab ?? storeTab;
  const hardware = hardwareFromStore ?? MOCK_HARDWARE;
  const activities = activitiesFromStore.length > 0 ? activitiesFromStore : MOCK_ACTIVITIES;

  return (
    <div className="flex h-full flex-col bg-white text-gray-900">
      {!hideTabs && (
        <div className="flex border-b border-gray-200">
          {(["performance", "security"] as Tab[]).map((tab) => (
            <button
              type="button"
              key={tab}
              onClick={() => dispatch(setActiveTab(tab))}
              className={`px-4 py-3 text-sm transition-colors ${
                activeTab === tab ? "border-b-2 border-blue-600 text-blue-600" : "text-gray-500 hover:text-gray-900"
              } ${variant === "full" ? "flex-1" : ""}`}
            >
              {tab === "performance" ? t("shell.performance") : t("shell.security")}
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 overflow-auto p-4 pt-6">
        {activeTab === "performance" ? (
          <PerformanceContent hardware={hardware} activities={activities} />
        ) : (
          <SecurityContent rateLimits={rateLimits} />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run monitor tests and verify they pass**

Run:

```bash
cd frontend && npm run test -- src/__tests__/components/monitor/MonitorPanel.test.tsx
```

Expected result: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
git status
```

Expected in this workspace: `fatal: not a git repository`. If Git is available in a future workspace, commit with:

```bash
git add frontend/src/components/monitor/MonitorPanel.tsx frontend/src/__tests__/components/monitor/MonitorPanel.test.tsx
git commit -m "feat: add compact light monitor panel"
```

---

## Task 5: Add compact Agent management mode

**Files:**
- Modify: `frontend/src/components/agent/AgentManagerUI.tsx`
- Modify: `frontend/src/__tests__/components/agent/AgentManagerUI.test.tsx`

- [ ] **Step 1: Add compact Agent tests**

Add these tests at the top of the `describe("AgentManagerUI", () => { ... })` block in `frontend/src/__tests__/components/agent/AgentManagerUI.test.tsx`:

```tsx
  it("renders compact agent manager for the right panel", () => {
    renderWithProviders(<AgentManagerUI variant="compact" />);

    expect(screen.getByText("数字主管")).toBeInTheDocument();
    expect(screen.getByText("风控顾问")).toBeInTheDocument();
    expect(screen.getByText("数据专家")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "+ New Agent" })).toBeInTheDocument();
  });

  it("compact agent mode opens templates", () => {
    renderWithProviders(<AgentManagerUI variant="compact" />);

    fireEvent.click(screen.getByRole("button", { name: "Templates" }));

    expect(screen.getByText("Template Library")).toBeInTheDocument();
    expect(screen.getByText("市场分析")).toBeInTheDocument();
  });
```

- [ ] **Step 2: Run Agent tests and verify compact prop fails before implementation**

Run:

```bash
cd frontend && npm run test -- src/__tests__/components/agent/AgentManagerUI.test.tsx
```

Expected result before implementation: FAIL because `variant` is not a supported prop.

- [ ] **Step 3: Add `variant` prop and compact classes to `AgentManagerUI.tsx`**

Modify `frontend/src/components/agent/AgentManagerUI.tsx` as follows.

First, add this interface before `export function AgentManagerUI()`:

```tsx
interface AgentManagerUIProps {
  variant?: "full" | "compact";
}
```

Then change the function signature from:

```tsx
export function AgentManagerUI() {
```

to:

```tsx
export function AgentManagerUI({ variant = "full" }: AgentManagerUIProps) {
```

Then replace the returned root/header/content class names in the function with these variant-aware versions:

```tsx
  const isCompact = variant === "compact";

  return (
    <div className="flex h-full flex-col bg-white text-gray-900">
      <div className={`${isCompact ? "border-b border-gray-200 p-3" : "h-12 border-b px-4"} flex items-center justify-between bg-white`}>
        {!isCompact && <h2 className="text-sm font-medium">{t("nav.agents")}</h2>}
        <div className="flex w-full gap-2">
          <button
            type="button"
            onClick={() => dispatch(setShowTemplates(!showTemplates))}
            className="rounded border border-gray-300 px-2 py-1 text-xs hover:bg-[#f7f8fa]"
          >
            Templates
          </button>
          <button
            type="button"
            onClick={() => dispatch(setEditingAgent("new"))}
            className="ml-auto rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700"
          >
            + New Agent
          </button>
        </div>
      </div>

      <div className={`${isCompact ? "space-y-3 p-3" : "space-y-4 p-4"} flex-1 overflow-y-auto`}>
```

Keep the existing search/filter, template library, editor, agent grid, and version-history logic inside this content block.

Inside the agent grid wrapper, change:

```tsx
        <div className="grid gap-3">
```

to:

```tsx
        <div className={isCompact ? "grid gap-2" : "grid gap-3"}>
```

Inside `AgentCard`, keep behavior unchanged but replace the root card class:

```tsx
    <div className="border rounded-lg p-4 bg-white dark:bg-gray-800 hover:shadow-md transition-shadow">
```

with:

```tsx
    <div className="rounded border border-gray-200 bg-white p-3 transition-shadow hover:shadow-sm">
```

- [ ] **Step 4: Run Agent tests and verify they pass**

Run:

```bash
cd frontend && npm run test -- src/__tests__/components/agent/AgentManagerUI.test.tsx
```

Expected result: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
git status
```

Expected in this workspace: `fatal: not a git repository`. If Git is available in a future workspace, commit with:

```bash
git add frontend/src/components/agent/AgentManagerUI.tsx frontend/src/__tests__/components/agent/AgentManagerUI.test.tsx
git commit -m "feat: add compact agent manager panel"
```

---

## Task 6: Rebuild LayoutShell as the prototype workspace

**Files:**
- Modify: `frontend/src/components/layout/LayoutShell.tsx`
- Test: `frontend/src/__tests__/components/layout/LayoutShell.test.tsx`

- [ ] **Step 1: Replace `LayoutShell.tsx` with the prototype workspace shell**

Replace the full contents of `frontend/src/components/layout/LayoutShell.tsx` with:

```tsx
import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { ChevronDown, Minus, Square, X, Zap } from "lucide-react";
import { t } from "@/i18n";
import { ConversationSidebar, ConversationWorkspace } from "@/components/conversation/ConversationUI";
import { AssetPanel } from "@/components/asset/AssetPanel";
import { MonitorPanel } from "@/components/monitor/MonitorPanel";
import { AgentManagerUI } from "@/components/agent/AgentManagerUI";

type LeftTab = "conversation" | "assets";
type RightTab = "performance" | "security" | "agent";

function ShellTab({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-4 py-3 text-sm transition-colors ${active ? "border-b-2 border-blue-600 text-blue-600" : "text-gray-500 hover:text-gray-900"}`}
    >
      {children}
    </button>
  );
}

export function LayoutShell() {
  const location = useLocation();
  const [leftTab, setLeftTab] = useState<LeftTab>("conversation");
  const [rightTab, setRightTab] = useState<RightTab>("performance");

  useEffect(() => {
    if (location.pathname.startsWith("/assets")) {
      setLeftTab("assets");
      return;
    }
    if (location.pathname.startsWith("/agents")) {
      setRightTab("agent");
      return;
    }
    if (location.pathname.startsWith("/monitor")) {
      setRightTab("performance");
    }
  }, [location.pathname]);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-white text-gray-900">
      <header className="flex h-10 shrink-0 items-center justify-between bg-blue-600 px-3 text-white">
        <div className="flex items-center gap-2">
          <div className="h-5 w-5 rounded-sm bg-white" />
          <span className="font-semibold">{t("shell.product")}</span>
          <span className="text-sm">{t("shell.version")}</span>
          <span className="text-xs opacity-70">{t("shell.workspace")}</span>
          <ChevronDown size={13} className="opacity-80" />
        </div>
        <div className="flex gap-3 text-sm">
          <Minus size={14} />
          <Square size={13} />
          <X size={14} />
        </div>
      </header>

      <div className="flex min-h-0 flex-1 overflow-hidden">
        <aside className="hidden w-[24%] min-w-[260px] flex-col border-r border-gray-200 bg-white md:flex">
          <div className="flex border-b border-gray-200">
            <ShellTab active={leftTab === "conversation"} onClick={() => setLeftTab("conversation")}>{t("nav.conversations")}</ShellTab>
            <ShellTab active={leftTab === "assets"} onClick={() => setLeftTab("assets")}>{t("nav.assets")}</ShellTab>
          </div>
          <div className="min-h-0 flex-1">
            {leftTab === "conversation" ? <ConversationSidebar /> : <AssetPanel variant="compact" />}
          </div>
        </aside>

        <main className="min-w-0 flex-1 basis-[60%]">
          <ConversationWorkspace />
        </main>

        <aside className="hidden w-[16%] min-w-[230px] flex-col border-l border-gray-200 bg-white xl:flex">
          <div className="flex border-b border-gray-200">
            <ShellTab active={rightTab === "performance"} onClick={() => setRightTab("performance")}>{t("shell.performance")}</ShellTab>
            <ShellTab active={rightTab === "security"} onClick={() => setRightTab("security")}>{t("shell.security")}</ShellTab>
            <ShellTab active={rightTab === "agent"} onClick={() => setRightTab("agent")}>{t("shell.agent")}</ShellTab>
          </div>
          <div className="min-h-0 flex-1">
            {rightTab === "performance" && <MonitorPanel variant="compact" activeTab="performance" hideTabs />}
            {rightTab === "security" && <MonitorPanel variant="compact" activeTab="security" hideTabs />}
            {rightTab === "agent" && <AgentManagerUI variant="compact" />}
          </div>
        </aside>
      </div>

      <footer className="flex h-9 shrink-0 items-center justify-between border-t border-gray-200 px-4 text-sm">
        <div className="flex items-center gap-1">
          <Zap size={15} className="text-blue-600" />
          {t("shell.statusApi")}
        </div>
        <div className="flex gap-5">
          <span>{t("shell.exportLogs")}</span>
          <span>{t("shell.ping")}</span>
        </div>
      </footer>
    </div>
  );
}
```

- [ ] **Step 2: Run the layout shell test and verify it passes**

Run:

```bash
cd frontend && npm run test -- src/__tests__/components/layout/LayoutShell.test.tsx
```

Expected result: PASS.

- [ ] **Step 3: Run the changed component tests together**

Run:

```bash
cd frontend && npm run test -- src/__tests__/components/layout/LayoutShell.test.tsx src/__tests__/components/conversation/ConversationUI.test.tsx src/__tests__/components/asset/AssetPanel.test.tsx src/__tests__/components/monitor/MonitorPanel.test.tsx src/__tests__/components/agent/AgentManagerUI.test.tsx
```

Expected result: PASS.

- [ ] **Step 4: Checkpoint**

Run:

```bash
git status
```

Expected in this workspace: `fatal: not a git repository`. If Git is available in a future workspace, commit with:

```bash
git add frontend/src/components/layout/LayoutShell.tsx frontend/src/__tests__/components/layout/LayoutShell.test.tsx
git commit -m "feat: rebuild app shell from prototype"
```

---

## Task 7: Full frontend verification and cleanup

**Files:**
- Verify all changed files from previous tasks.

- [ ] **Step 1: Run all frontend tests**

Run:

```bash
cd frontend && npm run test
```

Expected result: all Vitest suites pass.

- [ ] **Step 2: Run frontend lint**

Run:

```bash
cd frontend && npm run lint
```

Expected result: Biome check passes. If Biome reports formatting-only issues, run:

```bash
cd frontend && npm run lint:fix
```

Then re-run:

```bash
cd frontend && npm run lint
```

Expected result after fix: Biome check passes.

- [ ] **Step 3: Run production build**

Run:

```bash
cd frontend && npm run build
```

Expected result: TypeScript build and Vite production build complete successfully.

- [ ] **Step 4: Manual browser smoke check**

Run the dev server:

```bash
cd frontend && npm run dev -- --host 127.0.0.1
```

Open the printed local URL and verify:

- Top blue title bar shows `DeepSeek`, `V6.2.0`, and `NEXUS AI`.
- Left panel width resembles the prototype and contains `会话` / `资产` tabs.
- Clicking `资产` shows asset search and file list.
- Center panel shows the prototype task card, code row, success card, and input placeholder `输入您的问题...`.
- Right panel contains `性能` / `安全` / `Agent` tabs.
- Clicking `安全` shows rate limit and audit content.
- Clicking `Agent` shows the preset agents.
- Bottom status bar shows `DeepSeek API | API Key已配置`, `导出日志`, and `PING 15ms`.

Stop the dev server with `Ctrl+C` after checking.

- [ ] **Step 5: Final checkpoint**

Run:

```bash
git status
```

Expected in this workspace: `fatal: not a git repository`. If Git is available in a future workspace, commit with:

```bash
git add frontend/src/i18n.ts frontend/src/components frontend/src/__tests__/components
git commit -m "test: verify prototype shell redesign"
```

---

## Self-Review Notes

- Spec coverage: the plan covers the global shell, left conversation/assets tabs, center conversation workspace, right performance/security/Agent tabs, light prototype colors, route-to-tab activation, i18n strings, tests, lint, build, and manual smoke verification.
- Placeholder scan: the plan contains no unresolved placeholder tokens or open-ended implementation steps.
- Type consistency: tab types are `LeftTab = "conversation" | "assets"` and `RightTab = "performance" | "security" | "agent"`; component variant props are consistently `"full" | "compact"`; monitor controlled tabs are consistently `"performance" | "security"`.
