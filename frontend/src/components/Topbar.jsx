// src/components/Topbar.jsx
import React from "react";


export default function Topbar({ onOpenReport, onOpenAuth, metrics }) {
  const critical = metrics?.critical ?? 0;
  const moderate = metrics?.moderate ?? 0;
  const resolved = metrics?.resolved ?? 0;

  return (
    <header className="topbar">
      <div className="topbar-inner">
        <div className="brand">
          <div className="brand-logo">CW</div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>Crisis Mapping Dashboard</div>
            <div style={{ fontSize: 12, color: "#9aa7bf" }}>Real-time disaster response system</div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div className="inline-status" aria-hidden>
            <div style={{ fontSize: 13, color: "#e6eefc", marginRight: 8 }}>Live Updates Active</div>
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <div style={{ textAlign: "center" }}>
                <div style={{ color: "#ff6b6b", fontWeight: 700 }}>{critical}</div>
                <div style={{ fontSize: 12, color: "#9aa7bf" }}>Critical</div>
              </div>
              <div style={{ textAlign: "center" }}>
                <div style={{ color: "#f39c12", fontWeight: 700 }}>{moderate}</div>
                <div style={{ fontSize: 12, color: "#9aa7bf" }}>Moderate</div>
              </div>
              <div style={{ textAlign: "center" }}>
                <div style={{ color: "#27ae60", fontWeight: 700 }}>{resolved}</div>
                <div style={{ fontSize: 12, color: "#9aa7bf" }}>Resolved</div>
              </div>
            </div>
          </div>

          <div className="top-actions">
            <button className="btn ghost" title="Live updates">Live updates</button>
            <button className="btn top-report-btn" onClick={onOpenReport}>+ Report Incident</button>

            {/* account icon -> open auth modal */}
            <button
              className="btn ghost"
              style={{ borderRadius: 20, width: 40, height: 40, padding: 0 }}
              onClick={() => onOpenAuth("login")}
              title="Account"
            >
              <span style={{ width: "100%", display: "inline-block", textAlign: "center", color: "#9aa7bf" }}>👤</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
