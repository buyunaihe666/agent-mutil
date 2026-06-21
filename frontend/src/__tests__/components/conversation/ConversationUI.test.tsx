import { renderWithProviders } from "@/__tests__/test-utils";
import {
  ConversationSidebar,
  ConversationUI,
  ConversationWorkspace,
} from "@/components/conversation/ConversationUI";
import type { Message } from "@/features/conversation/conversationSlice";
import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

describe("ConversationUI", () => {
  it("renders the conversation workspace empty state when no active conversation", () => {
    renderWithProviders(<ConversationUI />);

    expect(screen.getByText("没有对话")).toBeInTheDocument();
    expect(screen.getByText("点击左侧「新建对话」按钮开始")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "新建对话" })).toBeInTheDocument();
  });

  it("renders conversation sidebar with empty state when no conversations", () => {
    renderWithProviders(<ConversationSidebar />);

    expect(screen.getByRole("button", { name: /新建对话/ })).toBeInTheDocument();
    expect(screen.getByText("暂无会话")).toBeInTheDocument();
    expect(screen.getByText("点击上方「新建对话」开始")).toBeInTheDocument();
  });

  it("uses Redux conversations instead of fallback conversation titles", () => {
    renderWithProviders(<ConversationSidebar />, {
      preloadedState: {
        conversation: {
          conversations: [
            {
              id: "custom-conversation",
              title: "自定义会话",
              status: "active",
              is_pinned: false,
              message_count: 0,
              updated_at: "2026-06-09T00:00:00.000Z",
            },
          ],
          activeConversationId: "custom-conversation",
          messages: {},
          isLoading: false,
          error: null,
        },
      },
    });

    expect(screen.getByText("自定义会话")).toBeInTheDocument();
    expect(screen.queryByText("代码审查讨论")).not.toBeInTheDocument();
  });

  it("clicking new conversation twice creates unique ids and activates the newest first item", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-09T00:00:00.000Z"));
    const randomSpy = vi.spyOn(Math, "random").mockReturnValue(0.123456);

    try {
      const { store } = renderWithProviders(<ConversationSidebar />);
      const newConversationButton = screen.getByRole("button", { name: /新建对话/ });

      fireEvent.click(newConversationButton);
      fireEvent.click(newConversationButton);

      const state = store.getState();
      const firstConversation = state.conversation.conversations[0];
      const secondConversation = state.conversation.conversations[1];

      expect(firstConversation).toBeDefined();
      expect(secondConversation).toBeDefined();
      expect(firstConversation.title).toBe("新建对话");
      expect(secondConversation.title).toBe("新建对话");
      expect(firstConversation.id).not.toBe(secondConversation.id);
      expect(state.conversation.activeConversationId).toBe(firstConversation.id);
    } finally {
      randomSpy.mockRestore();
      vi.useRealTimers();
    }
  });

  it("renders active conversation with messages in the workspace", () => {
    renderWithProviders(<ConversationWorkspace />, {
      preloadedState: {
        conversation: {
          conversations: [
            {
              id: "active-conv",
              title: "测试会话",
              status: "active" as const,
              is_pinned: false,
              message_count: 2,
              updated_at: "2026-06-09T00:00:00.000Z",
            },
          ],
          activeConversationId: "active-conv",
          messages: {
            "active-conv": [
              {
                id: "msg-1",
                role: "user" as const,
                content: "你好，帮我分析一下数据",
                created_at: "2026-06-09T00:00:00.000Z",
              },
              {
                id: "msg-2",
                role: "assistant" as const,
                content: "好的，我来分析数据",
                created_at: "2026-06-09T00:00:01.000Z",
              },
            ],
          },
          isLoading: false,
          error: null,
        },
      },
    });

    expect(screen.getByText("你好，帮我分析一下数据")).toBeInTheDocument();
    expect(screen.getByText("好的，我来分析数据")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("输入您的问题...")).toBeInTheDocument();
  });

  it("adds rapid user messages with unique ids to the normalized active conversation", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-09T00:00:00.000Z"));
    const randomSpy = vi.spyOn(Math, "random").mockReturnValue(0.654321);

    try {
      const { store } = renderWithProviders(<ConversationWorkspace />, {
        preloadedState: {
          conversation: {
            conversations: [
              {
                id: "available-conversation",
                title: "可用会话",
                status: "active",
                is_pinned: false,
                message_count: 0,
                updated_at: "2026-06-09T00:00:00.000Z",
              },
            ],
            activeConversationId: "missing-conversation",
            messages: {},
            isLoading: false,
            error: null,
          },
        },
      });

      const input = screen.getByPlaceholderText("输入您的问题...") as HTMLInputElement;
      const sendButton = screen.getByRole("button", { name: "发送" });

      fireEvent.change(input, { target: { value: "First rapid message" } });
      fireEvent.click(sendButton);
      fireEvent.change(input, { target: { value: "Second rapid message" } });
      fireEvent.click(sendButton);

      const state = store.getState();
      const activeMessages =
        state.conversation.messages["available-conversation"] ?? ([] as Message[]);

      expect(activeMessages).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ content: "First rapid message" }),
          expect.objectContaining({ content: "Second rapid message" }),
        ]),
      );
      expect(new Set(activeMessages.map((message: Message) => message.id)).size).toBe(
        activeMessages.length,
      );
      expect(input.value).toBe("");
    } finally {
      randomSpy.mockRestore();
      vi.useRealTimers();
    }
  });
});
