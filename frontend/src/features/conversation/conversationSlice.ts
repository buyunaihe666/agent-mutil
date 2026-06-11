import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";

export interface Conversation {
  id: string;
  title: string;
  status: string;
  is_pinned: boolean;
  message_count: number;
  updated_at: string;
}

export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  output?: string;
  error?: string;
  success?: boolean;
  status: "pending" | "running" | "complete" | "error";
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system" | "agent";
  content?: string;
  agent_id?: string;
  agent_name?: string;
  agent_emoji?: string;
  tool_calls?: ToolCall[];
  created_at: string;
}

interface ConversationState {
  conversations: Conversation[];
  activeConversationId: string | null;
  messages: Record<string, Message[]>; // conversationId -> messages
  isLoading: boolean;
  error: string | null;
}

const initialState: ConversationState = {
  conversations: [],
  activeConversationId: null,
  messages: {},
  isLoading: false,
  error: null,
};

export const conversationSlice = createSlice({
  name: "conversation",
  initialState,
  reducers: {
    setConversations: (state, action: PayloadAction<Conversation[]>) => {
      state.conversations = action.payload;
    },
    addConversation: (state, action: PayloadAction<Conversation>) => {
      state.conversations.unshift(action.payload);
    },
    updateConversation: (state, action: PayloadAction<Partial<Conversation> & { id: string }>) => {
      const idx = state.conversations.findIndex((c) => c.id === action.payload.id);
      if (idx !== -1) {
        state.conversations[idx] = { ...state.conversations[idx], ...action.payload };
      }
    },
    removeConversation: (state, action: PayloadAction<string>) => {
      state.conversations = state.conversations.filter((c) => c.id !== action.payload);
      if (state.activeConversationId === action.payload) {
        state.activeConversationId = null;
      }
      delete state.messages[action.payload];
    },
    setActiveConversation: (state, action: PayloadAction<string | null>) => {
      state.activeConversationId = action.payload;
    },
    togglePinConversation: (state, action: PayloadAction<string>) => {
      const conv = state.conversations.find((c) => c.id === action.payload);
      if (conv) {
        conv.is_pinned = !conv.is_pinned;
      }
    },
    setMessages: (
      state,
      action: PayloadAction<{ conversationId: string; messages: Message[] }>,
    ) => {
      state.messages[action.payload.conversationId] = action.payload.messages;
    },
    addMessage: (state, action: PayloadAction<{ conversationId: string; message: Message }>) => {
      const { conversationId, message } = action.payload;
      if (!state.messages[conversationId]) {
        state.messages[conversationId] = [];
      }
      state.messages[conversationId].push(message);
      // Update message count
      const conv = state.conversations.find((c) => c.id === conversationId);
      if (conv) {
        conv.message_count = state.messages[conversationId].length;
        conv.updated_at = new Date().toISOString();
      }
    },
    appendAgentDelta: (
      state,
      action: PayloadAction<{
        conversationId: string;
        delta: string;
        agentId?: string;
        agentName?: string;
        agentEmoji?: string;
        messageId?: string;
      }>,
    ) => {
      const { conversationId, delta, agentId, agentName, agentEmoji, messageId } = action.payload;
      if (!state.messages[conversationId]) {
        state.messages[conversationId] = [];
      }
      const msgs = state.messages[conversationId];
      // Find existing streaming assistant message or create new one
      // Use the messageId from backend to track the same message
      const lastMsg = msgs.length > 0 ? msgs[msgs.length - 1] : undefined;
      if (!lastMsg || lastMsg.role !== "assistant" || (messageId && lastMsg.id !== messageId)) {
        const newMsg: Message = {
          id: messageId ?? `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          role: "assistant",
          content: delta,
          agent_id: agentId,
          agent_name: agentName,
          agent_emoji: agentEmoji,
          created_at: new Date().toISOString(),
        };
        msgs.push(newMsg);
      } else {
        lastMsg.content = (lastMsg.content ?? "") + delta;
      }
    },
    finalizeAgentMessage: (
      state,
      action: PayloadAction<{
        conversationId: string;
        messageId?: string;
        content?: string;
      }>,
    ) => {
      const { conversationId, messageId, content } = action.payload;
      const msgs = state.messages[conversationId];
      if (!msgs) return;
      const target = messageId
        ? msgs.find((m) => m.id === messageId)
        : [...msgs].reverse().find((m) => m.role === "assistant");
      if (target && content) {
        target.content = content;
      }
      // Update message count
      const conv = state.conversations.find((c) => c.id === conversationId);
      if (conv) {
        conv.message_count = msgs.length;
        conv.updated_at = new Date().toISOString();
      }
    },
    addToolCall: (
      state,
      action: PayloadAction<{
        conversationId: string;
        toolCall: ToolCall;
      }>,
    ) => {
      const { conversationId, toolCall } = action.payload;
      if (!state.messages[conversationId]) {
        state.messages[conversationId] = [];
      }
      const msgs = state.messages[conversationId];
      // Find the last assistant message to attach the tool call to
      const lastAssistant = [...msgs].reverse().find((m) => m.role === "assistant");
      if (lastAssistant) {
        if (!lastAssistant.tool_calls) {
          lastAssistant.tool_calls = [];
        }
        // Replace or add
        const existingIdx = lastAssistant.tool_calls.findIndex((tc) => tc.id === toolCall.id);
        if (existingIdx >= 0) {
          lastAssistant.tool_calls[existingIdx] = toolCall;
        } else {
          lastAssistant.tool_calls.push(toolCall);
        }
      }
    },
    updateToolCall: (
      state,
      action: PayloadAction<{
        conversationId: string;
        toolCallId: string;
        updates: Partial<ToolCall>;
      }>,
    ) => {
      const { conversationId, toolCallId, updates } = action.payload;
      const msgs = state.messages[conversationId];
      if (!msgs) return;
      for (const msg of msgs) {
        if (msg.tool_calls) {
          const tc = msg.tool_calls.find((t) => t.id === toolCallId);
          if (tc) {
            Object.assign(tc, updates);
            return;
          }
        }
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const {
  setConversations,
  addConversation,
  updateConversation,
  removeConversation,
  setActiveConversation,
  togglePinConversation,
  setMessages,
  addMessage,
  appendAgentDelta,
  finalizeAgentMessage,
  addToolCall,
  updateToolCall,
  setLoading,
  setError,
} = conversationSlice.actions;

export default conversationSlice.reducer;
