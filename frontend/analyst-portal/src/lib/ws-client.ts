type MessageHandler = (event: MessageEvent) => void;

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private handlers = new Map<string, Set<MessageHandler>>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(url: string) {
    this.url = url;
  }

  connect(token: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    // Pass token via WebSocket subprotocol to avoid URL query parameter exposure
    // (tokens in URLs leak via browser history, proxy logs, and server access logs)
    this.ws = new WebSocket(this.url, [`access_token.${token}`]);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string);
        const channel = data.channel as string;
        this.handlers.get(channel)?.forEach((handler) => handler(event));
        this.handlers.get('*')?.forEach((handler) => handler(event));
      } catch {
        // Non-JSON message, forward to wildcard handlers
        this.handlers.get('*')?.forEach((handler) => handler(event));
      }
    };

    this.ws.onclose = () => {
      this.scheduleReconnect(token);
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  private scheduleReconnect(token: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;
    this.reconnectTimer = setTimeout(() => this.connect(token), delay);
  }

  subscribe(channel: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(channel)) {
      this.handlers.set(channel, new Set());
    }
    this.handlers.get(channel)!.add(handler);

    // Send subscription message
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: 'subscribe', channel }));
    }

    return () => {
      this.handlers.get(channel)?.delete(handler);
    };
  }

  disconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
    this.handlers.clear();
  }
}

let wsInstance: WebSocketManager | null = null;

export function getWebSocketManager(): WebSocketManager {
  if (!wsInstance) {
    const url = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8081';
    wsInstance = new WebSocketManager(url);
  }
  return wsInstance;
}
