import { WS_URL } from "../constants";

export function connectWebSocket(onMessage, onStatusChange) {
  const ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    if (onStatusChange) onStatusChange("connected");
  };

  ws.onclose = () => {
    if (onStatusChange) onStatusChange("disconnected");
  };

  ws.onerror = () => {
    if (onStatusChange) onStatusChange("error");
  };

  ws.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data);
      onMessage(payload);
    } catch {
      onMessage({ type: "raw", raw: event.data });
    }
  };

  const pingTimer = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send("ping");
    }
  }, 10000);

  return () => {
    clearInterval(pingTimer);
    ws.close();
  };
}
