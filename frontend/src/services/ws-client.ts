/** WebSocket client with heartbeat and exponential backoff reconnection. */

type MessageHandler = (data: unknown) => void;
type ConnectionHandler = () => void;

export class WSClient {
  private ws: WebSocket | null = null;
  private url: string;
  private heartbeatInterval = 30000;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectAttempts = 0;
  private maxReconnectDelay = 30000;
  private baseDelay = 1000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private messageHandlers: Map<string, Set<MessageHandler>> = new Map();
  private connectHandlers: Set<ConnectionHandler> = new Set();
  private disconnectHandlers: Set<ConnectionHandler> = new Set();
  private _intentionalClose = false;

  constructor(url: string) {
    this.url = url;
  }

  connect(): void {
    this._intentionalClose = false;
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this._startHeartbeat();
      for (const h of this.connectHandlers) h();
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string);
        const type = data.type as string;
        if (type === "pong") return;
        const handlers = this.messageHandlers.get(type);
        if (handlers) {
          for (const h of handlers) h(data);
        }
        // Also notify wildcard handlers
        const wildcard = this.messageHandlers.get("*");
        if (wildcard) {
          for (const h of wildcard) h(data);
        }
      } catch {
        // Ignore parse errors
      }
    };

    this.ws.onclose = () => {
      this._stopHeartbeat();
      for (const h of this.disconnectHandlers) h();
      if (!this._intentionalClose) {
        this._scheduleReconnect();
      }
    };

    this.ws.onerror = () => {
      // onclose will fire after this
    };
  }

  disconnect(): void {
    this._intentionalClose = true;
    this._stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
  }

  send(type: string, data?: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...data }));
    }
  }

  onMessage(type: string, handler: MessageHandler): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set());
    }
    this.messageHandlers.get(type)?.add(handler);
  }

  offMessage(type: string, handler: MessageHandler): void {
    this.messageHandlers.get(type)?.delete(handler);
  }

  onConnect(handler: ConnectionHandler): void {
    this.connectHandlers.add(handler);
  }

  offConnect(handler: ConnectionHandler): void {
    this.connectHandlers.delete(handler);
  }

  onDisconnect(handler: ConnectionHandler): void {
    this.disconnectHandlers.add(handler);
  }

  offDisconnect(handler: ConnectionHandler): void {
    this.disconnectHandlers.delete(handler);
  }

  private _startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      this.send("ping");
    }, this.heartbeatInterval);
  }

  private _stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private _scheduleReconnect(): void {
    const delay = Math.min(this.baseDelay * 2 ** this.reconnectAttempts, this.maxReconnectDelay);
    this.reconnectAttempts++;
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }
}
