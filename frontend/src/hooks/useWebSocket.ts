/** React hook wrapping WSClient for lifecycle-managed WebSocket connections. */

import { WSClient } from "@/services/ws-client";
import { useCallback, useEffect, useRef } from "react";

interface UseWebSocketOptions {
  url: string;
  onMessage?: (type: string, data: unknown) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoConnect?: boolean;
}

export function useWebSocket({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  autoConnect = true,
}: UseWebSocketOptions) {
  const clientRef = useRef<WSClient | null>(null);
  const handlersRef = useRef({ onMessage, onConnect, onDisconnect });
  handlersRef.current = { onMessage, onConnect, onDisconnect };

  useEffect(() => {
    const client = new WSClient(url);
    clientRef.current = client;

    client.onConnect(() => {
      handlersRef.current.onConnect?.();
    });

    client.onDisconnect(() => {
      handlersRef.current.onDisconnect?.();
    });

    client.onMessage("*", (data: unknown) => {
      const msg = data as { type?: string };
      handlersRef.current.onMessage?.(msg.type ?? "unknown", data);
    });

    if (autoConnect) {
      client.connect();
    }

    return () => {
      client.disconnect();
    };
  }, [url, autoConnect]);

  const send = useCallback((type: string, data?: Record<string, unknown>) => {
    clientRef.current?.send(type, data);
  }, []);

  const connect = useCallback(() => {
    clientRef.current?.connect();
  }, []);

  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
  }, []);

  return { send, connect, disconnect };
}
