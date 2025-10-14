// src/components/IncidentStatusBar.jsx
import React from "react";
import "./IncidentStatusBar.css";

export default function IncidentStatusBar({ stats = {}, onSelectSeverity }) {
  // stats: { critical, moderate, resolved, total }
  function handleClick(s) {
    window.dispatchEvent(
      new CustomEvent("map:filter", { detail: { severities: [s] } })
    );
    if (onSelectSeverity) onSelectSeverity(s);
  }

  return (
    <div className="incident-status-bar">
      <div
        className="status-card critical"
        role="button"
        onClick={() => handleClick("critical")}
      >
        <div className="count">{stats.critical ?? 0}</div>
        <div className="label">Critical</div>
      </div>
      <div
        className="status-card moderate"
        role="button"
        onClick={() => handleClick("moderate")}
      >
        <div className="count">{stats.moderate ?? 0}</div>
        <div className="label">Moderate</div>
      </div>
      <div
        className="status-card resolved"
        role="button"
        onClick={() => handleClick("resolved")}
      >
        <div className="count">{stats.resolved ?? 0}</div>
        <div className="label">Resolved</div>
      </div>
    </div>
  );
}
