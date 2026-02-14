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
            <div className="brand-title">Crisis Mapping Dashboard</div>
            <div className="brand-subtitle">Real-time disaster response system</div>
          </div>
        </div>

        <div className="topbar-actions">
          <div className="inline-status" aria-hidden>
            <div className="status-label">Live updates active</div>
            <div className="status-grid">
              <div className="status-item">
                <div className="status-value critical">{critical}</div>
                <div className="status-caption">Critical</div>
              </div>
              <div className="status-item">
                <div className="status-value moderate">{moderate}</div>
                <div className="status-caption">Moderate</div>
              </div>
              <div className="status-item">
                <div className="status-value resolved">{resolved}</div>
                <div className="status-caption">Resolved</div>
              </div>
            </div>
          </div>

          <div className="top-actions">
            <button className="btn ghost" title="Live updates">Live updates</button>
            <button className="btn top-report-btn" onClick={onOpenReport}>+ Report Incident</button>

            {/* account icon -> open auth modal */}
            <button
              className="btn ghost account-button"
              onClick={() => onOpenAuth("login")}
              title="Account"
            >
              <span className="account-icon">A</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
