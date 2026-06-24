/** Conversation UI - workspace conversation list and input. */

import {
  type Conversation,
  type Message,
  type ToolCall,
  addConversation,
  addMessage,
  addToolCall,
  updateToolCall,
  appendAgentDelta,
  finalizeAgentMessage,
  removeConversation,
  setActiveConversation,
  togglePinConversation,
  updateConversation,
} from "@/features/conversation/conversationSlice";
import { setSelectedAgent } from "@/features/agent/agentSlice";
import { t } from "@/i18n";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { AppDispatch, RootState } from "@/store";
import {
  ArrowRight,
  FileImage,
  MessageCircle,
  Paperclip,
  Pin,
  Plus,
  Radio,
  Terminal,
  Trash2,
  Bot,
} from "lucide-react";
import { type KeyboardEvent, useRef, useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { EmptyState } from "@/components/shared/EmptyState";
import { VoiceInput } from "./VoiceInput";

let idCounter = 0;

function createId(prefix: string) {
  idCounter += 1;
  return `${prefix}-${Date.now()}-${idCounter}-${Math.random().toString(36).slice(2, 8)}`;
}

function useConversationData() {
  const dispatch = useDispatch<AppDispatch>();
  const {
    conversations: conversationsFromStore,
    activeConversationId,
    messages,
  } = useSelector((state: RootState) => state.conversation);
  const selectedAgentId = useSelector((state: RootState) => state.agent.selectedAgentId);
  const agents = useSelector((state: RootState) => state.agent.agents);

  const conversations = conversationsFromStore;
  const normalizedActiveConvId =
    activeConversationId && conversations.some((c) => c.id === activeConversationId)
      ? activeConversationId
      : (conversations[0]?.id ?? null);
  const activeConvId = normalizedActiveConvId;
  const activeConv = activeConvId ? (conversations.find((c) => c.id === activeConvId) ?? null) : null;
  const activeMessages = activeConvId ? (messages[activeConvId] ?? []) : [];

  // WebSocket connection for agent communication
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = activeConvId ? `${protocol}//${window.location.host}/ws/chat/${activeConvId}` : "";

  const { send: wsSend } = useWebSocket({
    url: wsUrl,
    autoConnect: !!activeConvId,
    onMessage: (type: string, data: unknown) => {
      const msg = data as {
        type?: string;
        content?: string;
        delta?: string;
        agent_id?: string;
        agent_name?: string;
        agent_emoji?: string;
        message_id?: string;
        status?: string;
        error_message?: string;
        data?: {
          tool_call_id?: string;
          name?: string;
          arguments?: Record<string, unknown>;
          success?: boolean;
          output?: string;
          error?: string;
        };
      };

      if (!activeConvId) return;

      if (type === "agent_delta" && msg.delta) {
        dispatch(appendAgentDelta({
          conversationId: activeConvId,
          delta: msg.delta,
          agentId: msg.agent_id,
          agentName: msg.agent_name ?? "NEXUS AI",
          agentEmoji: msg.agent_emoji ?? "🤖",
          messageId: msg.message_id,
        }));
      } else if (type === "agent_message") {
        dispatch(finalizeAgentMessage({
          conversationId: activeConvId,
          messageId: msg.message_id,
          content: msg.content,
        }));
      } else if (type === "system") {
        dispatch(addMessage({
          conversationId: activeConvId,
          message: {
            id: msg.message_id ?? createId("sys"),
            role: "system",
            content: msg.content,
            created_at: new Date().toISOString(),
          },
        }));
      } else if (type === "agent_status") {
        // Status updates like "thinking" — could show an indicator
      } else if (type === "tool_call_start") {
        dispatch(addToolCall({
          conversationId: activeConvId,
          toolCall: {
            id: msg.data?.tool_call_id ?? `tc-${Date.now()}`,
            name: msg.data?.name ?? "unknown",
            arguments: msg.data?.arguments ?? {},
            status: "running",
          },
        }));
      } else if (type === "tool_call_result") {
        dispatch(updateToolCall({
          conversationId: activeConvId,
          toolCallId: msg.data?.tool_call_id ?? "",
          updates: {
            status: msg.data?.success ? "complete" : "error",
            output: msg.data?.output,
            error: msg.data?.error,
            success: msg.data?.success,
          },
        }));
      } else if (type === "error") {
        console.error("WebSocket error:", msg.error_message);
      }
    },
  });

  const handleNew = () => {
    const newConv: Conversation = {
      id: createId("conv"),
      title: t("shell.newConversation"),
      status: "active",
      is_pinned: false,
      message_count: 0,
      updated_at: new Date().toISOString(),
    };
    dispatch(addConversation(newConv));
    dispatch(setActiveConversation(newConv.id));
  };

  const handleSend = (content: string) => {
    if (!activeConvId) return;
    const messageId = createId("msg");
    // Get selected agent info for display
    const selectedAgent = agents.find((a) => a.id === selectedAgentId);
    dispatch(
      addMessage({
        conversationId: activeConvId,
        message: {
          id: messageId,
          role: "user",
          content,
          agent_id: selectedAgentId ?? undefined,
          agent_name: selectedAgent?.name,
          agent_emoji: selectedAgent?.avatar_emoji,
          created_at: new Date().toISOString(),
        },
      }),
    );
    // Auto-title: use first user message as conversation title (truncate to 30 chars)
    const msgs = messages[activeConvId] ?? [];
    if (msgs.length === 0) {
      const title = content.length > 30 ? content.slice(0, 30) + "..." : content;
      dispatch(updateConversation({ id: activeConvId, title }));
    }
    // Send via WebSocket to backend for agent response, with agent_id
    wsSend("user_message", {
      conversation_id: activeConvId,
      content,
      message_id: messageId,
      agent_id: selectedAgentId,
    });
  };

  const handlePin = (id: string) => {
    dispatch(togglePinConversation(id));
  };

  const handleDelete = (id: string) => {
    dispatch(removeConversation(id));
  };

  return {
    conversations,
    activeConvId,
    activeConv,
    activeMessages,
    onSelect: (id: string) => dispatch(setActiveConversation(id)),
    onNew: handleNew,
    onSend: handleSend,
    onPin: handlePin,
    onDelete: handleDelete,
  };
}

function ConversationItem({
  conv,
  active,
  onSelect,
  onPin,
  onDelete,
}: {
  conv: Conversation;
  active: boolean;
  onSelect: (id: string) => void;
  onPin: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(conv.id)}
      className={`group my-1.5 w-full rounded px-2 py-3 text-left text-sm transition-colors ${
        active ? "border-l-2 border-blue-600 bg-blue-50 text-gray-900" : "hover:bg-[#f7f8fa]"
      }`}
    >
      <div className="flex items-center gap-2">
        <MessageCircle
          aria-hidden="true"
          size={16}
          className={active ? "text-blue-600" : "text-gray-400"}
        />
        <span className="truncate flex-1">{conv.title || "Untitled"}</span>
        {/* Pin and delete — visible on hover */}
        <span className="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <span
            role="button"
            tabIndex={0}
            aria-label={conv.is_pinned ? "取消置顶" : "置顶"}
            onClick={(e) => { e.stopPropagation(); onPin(conv.id); }}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.stopPropagation(); onPin(conv.id); } }}
            className="p-0.5 rounded hover:bg-gray-200"
          >
            <Pin
              size={13}
              className={conv.is_pinned ? "fill-blue-500 text-blue-500" : "text-gray-400"}
            />
          </span>
          <span
            role="button"
            tabIndex={0}
            aria-label="删除"
            onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.stopPropagation(); onDelete(conv.id); } }}
            className="p-0.5 rounded hover:bg-red-100 text-gray-400 hover:text-red-500"
          >
            <Trash2 size={13} />
          </span>
        </span>
      </div>
      <div className="ml-6 mt-1 truncate text-xs text-gray-400">
        {active ? "自动分析已启动..." : `${conv.message_count} messages`}
      </div>
    </button>
  );
}

export function ConversationSidebar() {
  const { conversations, activeConvId, onSelect, onNew, onPin, onDelete } = useConversationData();
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
          <Plus aria-hidden="true" size={15} />
          {t("shell.newConversation")}
        </button>
      </div>

      <div className="flex-1 overflow-auto px-4 pb-4 pt-2">
        {conversations.length === 0 ? (
          <EmptyState
            icon="💬"
            title="暂无会话"
            description="点击上方「新建对话」开始"
          />
        ) : (
          <>
            {pinned.length > 0 && (
              <>
                <div className="mb-2 mt-4 text-xs text-gray-400">{t("shell.pinnedSpace")}</div>
                {pinned.map((conv) => (
                  <ConversationItem
                    key={conv.id}
                    conv={conv}
                    active={conv.id === activeConvId}
                    onSelect={onSelect}
                    onPin={onPin}
                    onDelete={onDelete}
                  />
                ))}
              </>
            )}

            {unpinned.length > 0 && (
              <>
                <div className="mb-2 mt-5 text-xs text-gray-400">{t("shell.activeConversations")}</div>
                {unpinned.map((conv) => (
                  <ConversationItem
                    key={conv.id}
                    conv={conv}
                    active={conv.id === activeConvId}
                    onSelect={onSelect}
                    onPin={onPin}
                    onDelete={onDelete}
                  />
                ))}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";

  return (
    <div className={`flex gap-3 px-4 py-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-200 text-sm">
        {isUser ? "👤" : (msg.agent_emoji ?? "🤖")}
      </div>
      <div className={`max-w-[75%] ${isUser ? "text-right" : "text-left"}`}>
        {msg.agent_name && <div className="mb-1 text-xs text-gray-500">{msg.agent_name}</div>}
        <div
          className={`rounded-lg px-4 py-2 text-sm ${isUser ? "bg-blue-600 text-white" : "bg-[#f7f8fa]"}`}
        >
          {msg.content ? (
            <div className="whitespace-pre-wrap break-words">{msg.content}</div>
          ) : (
            !msg.tool_calls && <div className="italic text-gray-400">...</div>
          )}
        </div>
        {/* Tool calls display */}
        {msg.tool_calls && msg.tool_calls.length > 0 && (
          <div className="mt-1 space-y-1">
            {msg.tool_calls.map((tc: ToolCall) => (
              <details key={tc.id} className="rounded border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs">
                <summary className="cursor-pointer text-gray-500 hover:text-gray-700 select-none">
                  <span className="mr-1">
                    {tc.status === "running" ? "⏳" : tc.status === "complete" ? "✅" : "❌"}
                  </span>
                  <span className="font-medium">Tool: {tc.name}</span>
                </summary>
                <div className="mt-1.5 space-y-1 text-gray-600">
                  <div>
                    <span className="font-medium">Arguments:</span>
                    <pre className="mt-0.5 overflow-x-auto rounded bg-gray-100 px-2 py-1 text-xs">
                      {JSON.stringify(tc.arguments, null, 2)}
                    </pre>
                  </div>
                  {tc.output && (
                    <div>
                      <span className="font-medium">Result:</span>
                      <pre className="mt-0.5 overflow-x-auto rounded bg-gray-100 px-2 py-1 text-xs">
                        {tc.output}
                      </pre>
                    </div>
                  )}
                  {tc.error && (
                    <div className="text-red-500">
                      <span className="font-medium">Error:</span> {tc.error}
                    </div>
                  )}
                </div>
              </details>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ChatInput({ onSend }: { onSend: (content: string) => void }) {
  const [value, setValue] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

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

  const handleVoiceTranscription = (text: string) => {
    setValue((prev) => (prev ? prev + " " + text : text));
  };

  const handleFileAttach = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      // v1: file attachment — log for now, future: upload to asset store
      console.log("File attached:", files[0]?.name);
    }
    e.target.value = "";
  };

  return (
    <div className="border-t border-gray-200 p-4">
      <div className="mb-3 flex items-center gap-3 text-gray-500">
        <span title="上传文件">
          <Paperclip
            aria-hidden="true"
            size={17}
            className="cursor-pointer hover:text-blue-600 transition-colors"
            onClick={() => fileInputRef.current?.click()}
          />
        </span>
        <span title="上传图片">
          <FileImage
            aria-hidden="true"
            size={17}
            className="cursor-pointer hover:text-blue-600 transition-colors"
            onClick={() => imageInputRef.current?.click()}
          />
        </span>
        {/* VoiceInput replaces disabled Mic */}
        <VoiceInput onTranscription={handleVoiceTranscription} />
        <span title="实时广播 (即将上线)">
          <Radio
            aria-hidden="true"
            size={17}
            className="text-gray-300 cursor-not-allowed"
          />
        </span>
        <span title="命令行模式 (即将上线)">
          <Terminal
            aria-hidden="true"
            size={17}
            className="text-gray-300 cursor-not-allowed"
          />
        </span>
        {/* Hidden file inputs */}
        <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileAttach} />
        <input ref={imageInputRef} type="file" accept="image/*" className="hidden" onChange={handleFileAttach} />
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
          <ArrowRight aria-hidden="true" size={17} />
        </button>
      </div>
    </div>
  );
}

export function ConversationWorkspace() {
  const { onSend, onNew } = useConversationData();
  const dispatch = useDispatch<AppDispatch>();
  const selectedAgentId = useSelector((state: RootState) => state.agent.selectedAgentId);
  const agentsFromStore = useSelector((state: RootState) => state.agent.agents);
  const activeMessages = useSelector((state: RootState) => {
    const convId = state.conversation.activeConversationId;
    if (!convId) return [];
    return state.conversation.messages[convId] ?? [];
  });
  const activeConvId = useSelector((state: RootState) => state.conversation.activeConversationId);
  // Fallback to mock agents if store is empty (same pattern as AgentManagerUI)
  const agentList = agentsFromStore.length > 0 ? agentsFromStore : [
    { id: "1", name: "数字主管", avatar_emoji: "🎯", is_active: true },
    { id: "2", name: "风控顾问", avatar_emoji: "🛡️", is_active: true },
    { id: "3", name: "数据专家", avatar_emoji: "📊", is_active: true },
  ];
  const activeAgents = agentList.filter((a: { is_active?: boolean }) => a.is_active !== false);
  const selectedAgent = activeAgents.find((a: { id: string }) => a.id === selectedAgentId) ?? activeAgents[0] ?? null;

  // Auto-select first agent if none selected
  useEffect(() => {
    if (!selectedAgentId && activeAgents.length > 0) {
      dispatch(setSelectedAgent(activeAgents[0].id));
    }
  }, [selectedAgentId, activeAgents, dispatch]);

  return (
    <div className="flex h-full flex-col bg-white">
      {/* Agent Selector Header */}
      {activeConvId && selectedAgent && (
        <div className="flex items-center gap-2 border-b border-gray-200 px-4 py-2">
          <Bot size={16} className="text-gray-400" />
          <select
            value={selectedAgentId ?? ""}
            onChange={(e) => dispatch(setSelectedAgent(e.target.value || null))}
            className="flex-1 rounded border border-gray-200 bg-gray-50 px-2 py-1 text-sm text-gray-700 outline-none focus:border-blue-500"
          >
            {activeAgents.map((a: { id: string; name: string; avatar_emoji?: string }) => (
              <option key={a.id} value={a.id}>
                {a.avatar_emoji ?? "🤖"} {a.name}
              </option>
            ))}
          </select>
        </div>
      )}
      <div className="flex-1 overflow-auto p-5">
        {activeConvId ? (
          activeMessages.length === 0 ? (
            <EmptyState
              icon="💬"
              title="开始对话"
              description="输入您的问题开始与AI协作"
            />
          ) : (
            activeMessages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))
          )
        ) : (
          <EmptyState
            icon="💬"
            title="没有对话"
            description="点击左侧「新建对话」按钮开始"
            action={{ label: "新建对话", onClick: onNew }}
          />
        )}
      </div>
      {activeConvId && <ChatInput onSend={onSend} />}
    </div>
  );
}

export function ConversationUI() {
  return <ConversationWorkspace />;
}
