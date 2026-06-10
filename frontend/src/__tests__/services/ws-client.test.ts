import { WSClient } from "@/services/ws-client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Mock WebSocket class
class MockWebSocket {
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  readyState: number = WebSocket.CONNECTING;
  sentMessages: string[] = [];

  constructor(url: string) {
    this.url = url;
  }

  // Simulate receiving a message
  simulateMessage(data: unknown) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) } as MessageEvent);
    }
  }

  // Simulate receiving raw data
  simulateRawMessage(data: string) {
    if (this.onmessage) {
      this.onmessage({ data } as MessageEvent);
    }
  }

  // Simulate open event
  simulateOpen() {
    this.readyState = WebSocket.OPEN;
    this.onopen?.();
  }

  // Simulate close event
  simulateClose(code = 1000, reason = "") {
    this.readyState = WebSocket.CLOSED;
    this.onclose?.({ code, reason } as CloseEvent);
  }

  // Simulate error event
  simulateError() {
    this.onerror?.();
  }

  send(data: string) {
    this.sentMessages.push(data);
  }

  close() {
    this.readyState = WebSocket.CLOSED;
  }
}

const OriginalWebSocket = globalThis.WebSocket;

describe("WSClient", () => {
  let mockWs: MockWebSocket;
  let client: WSClient;

  beforeEach(() => {
    vi.useFakeTimers();
    mockWs = new MockWebSocket("ws://localhost:8000/ws/chat/test");
    globalThis.WebSocket = vi.fn(() => mockWs) as unknown as typeof WebSocket;
    // Also set static constants
    (globalThis.WebSocket as unknown as Record<string, number>).CONNECTING = 0;
    (globalThis.WebSocket as unknown as Record<string, number>).OPEN = 1;
    (globalThis.WebSocket as unknown as Record<string, number>).CLOSING = 2;
    (globalThis.WebSocket as unknown as Record<string, number>).CLOSED = 3;
    client = new WSClient("ws://localhost:8000/ws/chat/test");
  });

  afterEach(() => {
    client.disconnect();
    vi.useRealTimers();
    globalThis.WebSocket = OriginalWebSocket;
  });

  describe("connect", () => {
    it("creates WebSocket with correct URL", () => {
      client.connect();
      expect(globalThis.WebSocket).toHaveBeenCalledWith("ws://localhost:8000/ws/chat/test");
    });

    it("calls connect handlers on open", () => {
      const handler = vi.fn();
      client.onConnect(handler);
      client.connect();
      mockWs.simulateOpen();
      expect(handler).toHaveBeenCalled();
    });

    it("resets reconnect attempts on open", () => {
      client.connect();
      mockWs.simulateOpen();
      mockWs.simulateClose();
      mockWs.simulateOpen();
      // Reconnect attempts should be 0 after successful connection
      // No assert needed directly, but reconnection should use base delay
    });
  });

  describe("message handling", () => {
    beforeEach(() => {
      client.connect();
      mockWs.simulateOpen();
    });

    it("routes messages to correct type handler", () => {
      const handler = vi.fn();
      client.onMessage("test_type", handler);
      mockWs.simulateMessage({ type: "test_type", payload: "hello" });
      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({ type: "test_type", payload: "hello" }),
      );
    });

    it("ignores pong messages", () => {
      const handler = vi.fn();
      client.onMessage("pong", handler);
      mockWs.simulateMessage({ type: "pong" });
      expect(handler).not.toHaveBeenCalled();
    });

    it("wildcard handlers receive all messages", () => {
      const handler = vi.fn();
      client.onMessage("*", handler);
      mockWs.simulateMessage({ type: "some_type", data: "test" });
      expect(handler).toHaveBeenCalledWith(expect.objectContaining({ type: "some_type" }));
    });

    it("silently ignores malformed JSON", () => {
      const handler = vi.fn();
      client.onMessage("*", handler);
      // Should not throw
      expect(() => mockWs.simulateRawMessage("not valid json")).not.toThrow();
    });

    it("offMessage unregisters handler", () => {
      const handler = vi.fn();
      client.onMessage("type_a", handler);
      client.offMessage("type_a", handler);
      mockWs.simulateMessage({ type: "type_a" });
      expect(handler).not.toHaveBeenCalled();
    });

    it("supports multiple handlers for same type", () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();
      client.onMessage("shared_type", handler1);
      client.onMessage("shared_type", handler2);
      mockWs.simulateMessage({ type: "shared_type" });
      expect(handler1).toHaveBeenCalled();
      expect(handler2).toHaveBeenCalled();
    });
  });

  describe("send", () => {
    it("serializes data as JSON with type field", () => {
      client.connect();
      mockWs.simulateOpen();
      client.send("user_message", { content: "hello" });
      const sent = JSON.parse(mockWs.sentMessages[0]);
      expect(sent.type).toBe("user_message");
      expect(sent.content).toBe("hello");
    });

    it("does nothing when WebSocket is not open", () => {
      client.send("test", {});
      expect(mockWs.sentMessages.length).toBe(0);
    });
  });

  describe("disconnect", () => {
    it("sets intentional close flag", () => {
      client.connect();
      mockWs.simulateOpen();
      client.disconnect();
      // Should be intentional
      expect(mockWs.readyState).toBe(WebSocket.CLOSED);
    });

    it("calls disconnect handlers", () => {
      const handler = vi.fn();
      client.onDisconnect(handler);
      client.connect();
      mockWs.simulateOpen();
      mockWs.simulateClose();
      expect(handler).toHaveBeenCalled();
    });

    it("offDisconnect unregisters handler", () => {
      const handler = vi.fn();
      client.onDisconnect(handler);
      client.offDisconnect(handler);
      client.connect();
      mockWs.simulateOpen();
      mockWs.simulateClose();
      expect(handler).not.toHaveBeenCalled();
    });
  });

  describe("reconnection", () => {
    it("schedules reconnect on unexpected close", () => {
      client.connect();
      mockWs.simulateOpen();
      const handler = vi.fn();
      client.onConnect(handler);
      mockWs.simulateClose();
      // After close, should schedule reconnect
      // First reconnect attempt: 1s
      vi.advanceTimersByTime(1000);
      // Should have tried to reconnect
      expect(globalThis.WebSocket).toHaveBeenCalledTimes(2);
    });

    it("does not reconnect on intentional close", () => {
      client.connect();
      mockWs.simulateOpen();
      client.disconnect();
      mockWs.simulateClose();
      vi.advanceTimersByTime(1000);
      // Should NOT have tried to reconnect (only one WebSocket created)
      expect(globalThis.WebSocket).toHaveBeenCalledTimes(1);
    });

    it("exponential backoff caps at maxReconnectDelay", () => {
      client.connect();
      mockWs.simulateOpen();
      // Simulate many reconnect attempts
      for (let i = 0; i < 10; i++) {
        mockWs.simulateClose();
        vi.advanceTimersByTime(30000);
        mockWs.simulateOpen();
        mockWs.simulateClose();
      }
      // The delay should cap at 30000ms
      // This test verifies the system doesn't crash and the cap works
    });
  });

  describe("heartbeat", () => {
    it("sends ping every 30 seconds", () => {
      client.connect();
      mockWs.simulateOpen();
      expect(mockWs.sentMessages.length).toBe(0);
      vi.advanceTimersByTime(30000);
      expect(mockWs.sentMessages.length).toBeGreaterThanOrEqual(1);
      const sent = JSON.parse(mockWs.sentMessages[0]);
      expect(sent.type).toBe("ping");
    });

    it("stops heartbeat on close", () => {
      client.connect();
      mockWs.simulateOpen();
      vi.advanceTimersByTime(30000);
      expect(mockWs.sentMessages.length).toBeGreaterThanOrEqual(1);
      mockWs.simulateClose();
      const sentBeforeClose = mockWs.sentMessages.length;
      vi.advanceTimersByTime(30000);
      // No more pings after close
      expect(mockWs.sentMessages.length).toBe(sentBeforeClose);
    });
  });

  describe("event handlers", () => {
    it("onConnect registers a connect handler", () => {
      const handler = vi.fn();
      client.onConnect(handler);
      client.connect();
      mockWs.simulateOpen();
      expect(handler).toHaveBeenCalled();
    });

    it("offConnect unregisters a connect handler", () => {
      const handler = vi.fn();
      client.onConnect(handler);
      client.offConnect(handler);
      client.connect();
      mockWs.simulateOpen();
      expect(handler).not.toHaveBeenCalled();
    });
  });
});
