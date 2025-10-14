// src/components/IncidentsSocket.jsx
import React, { useEffect, useRef } from "react";

const API = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function IncidentsSocket() {
  const wsRef = useRef(null);

  useEffect(() => {
    // build ws URL (http -> ws)
    let base = API;
    if (base.endsWith("/")) base = base.slice(0, -1);
    const wsBase = base.replace(/^http/, "ws");
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const q = token ? `?token=${encodeURIComponent(token)}` : "";
    const url = `${wsBase}/ws/incidents${q}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.info("Incidents WS connected");
    };

    ws.onmessage = (ev) => {
      try {
        const payload = JSON.parse(ev.data);
        // If server sends the structured payload (type = "incident_created")
        if (payload && payload.type === "incident_created") {
          const inc = payload.incident;
          // Build feature shape like geojson feature the rest of UI expects
          const feature = {
            type: "Feature",
            properties: {
              id: inc.id,
              title: inc.title,
              description: inc.description,
              disaster_type: inc.disaster_type,
              credibility_score: inc.credibility_score,
              severity: inc.severity,
              created_at: inc.created_at,
            },
            geometry: {
              type: "Point",
              coordinates: [inc.lon, inc.lat],
            },
          };

          // incidents:update used by your Sidebar to update recent list and counts
          window.dispatchEvent(new CustomEvent("incidents:update", {
            detail: { incidents: [feature], counts: payload.counts }
          }));

          // incident:created (for immediate map addition if you use that)
          window.dispatchEvent(new CustomEvent("incident:created", { detail: feature }));
        } else {
          // If message structure different, just emit update event with raw payload
          window.dispatchEvent(new CustomEvent("incidents:update", { detail: payload }));
        }
      } catch (err) {
        console.error("Error parsing WS message", err);
      }
    };

    ws.onclose = () => {
      console.info("Incidents WS disconnected");
    };

    ws.onerror = (e) => {
      console.error("Incidents WS error", e);
    };

    return () => {
      try { ws.close(); } catch (e) {}
    };
  }, []);

  return null; // no UI
}
