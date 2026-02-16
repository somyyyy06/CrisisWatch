const isLocalhost =
  typeof window !== "undefined" && window.location.hostname === "localhost";

const API_BASE =
  process.env.REACT_APP_API_URL ||
  (isLocalhost ? "http://127.0.0.1:8000" : "");

// For WebSocket: convert http/https to ws/wss dynamically
const WS_BASE = process.env.REACT_APP_WS_URL || (() => {
  if (!API_BASE) return "";
  // If we have an API_BASE, convert protocol for WebSocket
  return API_BASE.replace(/^http/, "ws");
})();

if (!API_BASE && !isLocalhost) {
  // eslint-disable-next-line no-console
  console.error("REACT_APP_API_URL is not set. Check your Vercel env vars.");
}

export { API_BASE, WS_BASE };
