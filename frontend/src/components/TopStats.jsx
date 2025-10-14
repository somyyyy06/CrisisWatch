// src/components/TopStats.jsx
import React, { useEffect, useState } from "react";

const API = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

function StatCard({ title, big, sub, color }) {
  return (
    <div className="stat-card">
      <div className="stat-title">{title}</div>
      <div className="stat-big" style={{ color: color || "white" }}>{big}</div>
      {sub ? <div className="stat-sub">{sub}</div> : null}
    </div>
  );
}

export default function TopStats() {
  const [metrics, setMetrics] = useState({
    active_incidents: 0,
    total_incidents: 0,
    ai_accuracy: 0.75,
    response_time: "0.0m",
    data_sources: 0,
    critical: 0,
    moderate: 0,
    resolved: 0,
  });

  async function fetchMetrics() {
    try {
      const resp = await fetch(`${API}/metrics/summary`);
      if (!resp.ok) return;
      const data = await resp.json();
      setMetrics((prev) => ({ ...prev, ...data }));
    } catch {
      // ignore errors
    }
  }

  useEffect(() => {
    fetchMetrics();
    const id = setInterval(fetchMetrics, 15000);
    return () => clearInterval(id);
  }, []);

  // 🔑 Update counts live when incidents update
  useEffect(() => {
    const handler = (e) => {
      const d = e.detail || {};
      if (d.counts) {
        const c = d.counts;
        setMetrics((prev) => ({
          ...prev,
          critical: c.critical,
          moderate: c.moderate,
          resolved: c.resolved,
          active_incidents: c.critical + c.moderate,
          total_incidents: c.total,
        }));
      }
    };
    window.addEventListener("incidents:update", handler);
    return () => window.removeEventListener("incidents:update", handler);
  }, []);

  return (
    <div className="top-stats-wrap">
      <div className="top-stats">
        <StatCard
          title="Critical"
          big={metrics.critical}
          sub="Live reports"
          color="#ff5c6c"
        />
        <StatCard
          title="Moderate"
          big={metrics.moderate}
          sub="Live reports"
          color="#ffd166"
        />
        <StatCard
          title="Resolved"
          big={metrics.resolved}
          sub="Handled cases"
          color="#9df7b4"
        />
        <StatCard
          title="Total Incidents"
          big={metrics.total_incidents}
          sub="Across all types"
          color="#6fc3ff"
        />
      </div>
    </div>
  );
}
