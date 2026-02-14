// src/components/Sidebar.jsx
import React, { useEffect, useState } from "react";

const INCIDENT_TYPES = ["Wildfire", "Flood", "Earthquake", "Crime", "Traffic", "Power Outage"];
const TIME_RANGES = [
  { value: "all", label: "All time" },
  { value: "24h", label: "Last 24 hours" },
  { value: "3d", label: "Last 3 days" },
  { value: "1w", label: "Last week" },
  { value: "1m", label: "Last month" },
];

// helper to map credibility → severity
function mapCredibilityToSeverity(score) {
  if (score === null || score === undefined) return "unknown";
  if (score >= 0.7) return "critical";
  if (score >= 0.4) return "moderate";
  return "resolved";
}

export default function Sidebar() {
  const [types, setTypes] = useState([]);
  const [severities, setSeverities] = useState([]);
  const [timeRange, setTimeRange] = useState("all");
  const [allIncidents, setAllIncidents] = useState([]);

  function filterByTime(incident) {
    if (timeRange === "all") return true;
    const now = new Date();
    const d = new Date(incident.created_at);
    if (timeRange === "24h") return now - d < 24 * 60 * 60 * 1000;
    if (timeRange === "3d") return now - d < 3 * 24 * 60 * 60 * 1000;
    if (timeRange === "1w") return now - d < 7 * 24 * 60 * 60 * 1000;
    if (timeRange === "1m") return now - d < 30 * 24 * 60 * 60 * 1000;
    return true;
  }

  const filtered = allIncidents
    .filter((it) => (types.length === 0 ? true : types.includes(it.type)))
    .filter((it) => (severities.length === 0 ? true : severities.includes(it.severity)))
    .filter((it) => filterByTime(it));

  // 🔑 Compute and dispatch counts
  function updateCounts(list) {
    const counts = { critical: 0, moderate: 0, resolved: 0, total: list.length };
    list.forEach((it) => {
      if (it.severity === "critical") counts.critical++;
      else if (it.severity === "moderate") counts.moderate++;
      else if (it.severity === "resolved") counts.resolved++;
    });
    window.dispatchEvent(new CustomEvent("incidents:update", { detail: { counts } }));
  }

  // Listen for incidents
  useEffect(() => {
    const onUpdate = (e) => {
      const { incidents } = e.detail || {};
      if (incidents) {
        const list = (incidents || []).map((f) => {
          const cred = f.properties?.credibility_score;
          return {
            id: f.properties?.id,
            title: f.properties?.title,
            type: f.properties?.disaster_type,
            created_at: f.properties?.created_at,
            credibility: cred,
            severity: mapCredibilityToSeverity(cred),
            lat: f.geometry?.coordinates?.[1],
            lon: f.geometry?.coordinates?.[0],
          };
        });
        setAllIncidents((prev) => {
          const merged = [...list, ...prev];
          updateCounts(merged);
          return merged;
        });
      }
    };

    const onCreated = (e) => {
      const f = e.detail;
      if (!f) return;
      const cred = f.properties?.credibility_score;
      const inc = {
        id: f.properties?.id,
        title: f.properties?.title,
        type: f.properties?.disaster_type,
        created_at: f.properties?.created_at,
        credibility: cred,
        severity: mapCredibilityToSeverity(cred),
        lat: f.geometry?.coordinates?.[1],
        lon: f.geometry?.coordinates?.[0],
      };
      setAllIncidents((prev) => {
        const merged = [inc, ...prev];
        updateCounts(merged);
        return merged;
      });
    };

    // 🔑 Handle incident resolution
    const onResolved = (e) => {
      const { id } = e.detail || {};
      if (!id) return;
      setAllIncidents((prev) => {
        const updated = prev.map((it) =>
          it.id === id ? { ...it, severity: "resolved" } : it
        );
        updateCounts(updated);
        return updated;
      });
    };

    window.addEventListener("incidents:update", onUpdate);
    window.addEventListener("incident:created", onCreated);
    window.addEventListener("incident:resolved", onResolved);

    return () => {
      window.removeEventListener("incidents:update", onUpdate);
      window.removeEventListener("incident:created", onCreated);
      window.removeEventListener("incident:resolved", onResolved);
    };
  }, []);

  function toggleType(t) {
    const next = types.includes(t) ? types.filter((x) => x !== t) : [...types, t];
    setTypes(next);
  }

  function toggleSeverity(s) {
    const next = severities.includes(s) ? severities.filter((x) => x !== s) : [...severities, s];
    setSeverities(next);
  }

  function onTimeChange(e) {
    setTimeRange(e.target.value);
  }

  function focusIncident(item) {
    if (!item) return;
    window.dispatchEvent(
      new CustomEvent("map:zoomTo", {
        detail: { lat: item.lat, lon: item.lon, zoom: 13 },
      })
    );
  }

  return (
    <div className="sidebar">
      <div className="sidebar-section">
        <h3>Filters and search</h3>
        <div className="sidebar-search">
          <input placeholder="Search incidents, locations..." />
        </div>

        <div className="filter-title">Incident type</div>
        {INCIDENT_TYPES.map((t) => (
          <div key={t} className="filter-row">
            <input
              className="filter-checkbox"
              type="checkbox"
              id={`t-${t}`}
              checked={types.includes(t)}
              onChange={() => toggleType(t)}
            />
            <label htmlFor={`t-${t}`}>{t}</label>
          </div>
        ))}

        <div className="filter-title">Severity</div>
        <div className="severity-buttons">
          <button className="btn ghost" onClick={() => toggleSeverity("critical")}>
            Critical
          </button>
          <button className="btn ghost" onClick={() => toggleSeverity("moderate")}>
            Moderate
          </button>
          <button className="btn ghost" onClick={() => toggleSeverity("resolved")}>
            Resolved
          </button>
        </div>

        <div className="filter-title">Time range</div>
        <select
          className="time-range-select"
          value={timeRange}
          onChange={onTimeChange}
        >
          {TIME_RANGES.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>
      </div>

      <div className="sidebar-section recent-section">
        <h3>Recent incidents</h3>
        {filtered.length === 0 ? (
          <div className="empty-state">
            No incidents found matching your filters
          </div>
        ) : (
          <div className="incident-list">
            {filtered.slice(0, 12).map((it) => (
              <div
                key={it.id || it.title}
                className="incident-card"
                onClick={() => focusIncident(it)}
              >
                <div className="incident-title">
                  {it.title || it.type || "Incident"}
                </div>
                <div className="incident-meta">
                  {it.type} • {new Date(it.created_at || Date.now()).toLocaleString()}
                </div>
                <div className="incident-meta">
                  Severity: {it.severity} • Cred:{" "}
                  {it.credibility || it.credibility === 0 ? it.credibility.toFixed(2) : "-"}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
