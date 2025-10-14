// src/components/PerformanceMetrics.jsx
import React from "react";

function Bar({ value = 50, colorStart = "#2F80ED", colorEnd = "#2AA7FF" }) {
  return (
    <div style={{ background: "rgba(255,255,255,0.03)", height: 10, borderRadius: 8, overflow: "hidden" }}>
      <div style={{ width: `${Math.max(0, Math.min(100, value))}%`, height: "100%", background: `linear-gradient(90deg, ${colorStart}, ${colorEnd})` }} />
    </div>
  );
}

export default function PerformanceMetrics({ metrics = { apiTime: 142, accuracy: 75, dataProcessing: 76 } }) {
  return (
    <div style={{ marginTop: 18 }}>
      <h3>Performance Metrics</h3>
      <div style={{ marginTop: 8, fontSize: 13, color: "#9aa7bf" }}>API Response Time</div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 6 }}>
        <Bar value={Math.max(0, Math.min(100, 100 - (metrics.apiTime / 5)))} />
        <div style={{ marginLeft: 10, color: "#2dd36f", fontWeight: 700 }}>{metrics.apiTime}ms</div>
      </div>

      <div style={{ marginTop: 12, fontSize: 13, color: "#9aa7bf" }}>ML Model Accuracy</div>
      <div style={{ marginTop: 6 }}>
        <Bar value={metrics.accuracy} />
      </div>

      <div style={{ marginTop: 12, fontSize: 13, color: "#9aa7bf" }}>Data Processing</div>
      <div style={{ marginTop: 6 }}>
        <Bar value={metrics.dataProcessing} colorStart="#ffd166" colorEnd="#ff7f0e" />
      </div>

      <div style={{ marginTop: 10, color: "#9aa7bf", fontSize: 13 }}>
        <div>Total incidents today: 0</div>
        <div>Avg. response time: 4.2 minutes</div>
        <div>False positives: 2.1%</div>
      </div>
    </div>
  );
}
