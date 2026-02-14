// src/components/RightPanel.jsx
import React, { useState } from "react";
import PerformanceMetrics from "./PerformanceMetrics";

const API =
  process.env.REACT_APP_API_URL ||
  (window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000"
    : "https://crisiswatch.onrender.com");

export default function RightPanel({ metrics, feed }) {
  const m = metrics || { apiTime: 142, accuracy: 75, dataProcessing: 76 };

  // 🔹 State for Summary Generator
  const [inputText, setInputText] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);

  // 🔹 Call backend summarization API
  const handleSummarize = async () => {
    if (!inputText.trim()) return;
    setLoading(true);
    setSummary(""); // clear old result
    try {
      const response = await fetch(`${API}/summarize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: inputText }),
      });
      const data = await response.json();
      setSummary(data.summary || "No summary generated.");
    } catch (err) {
      console.error("Error summarizing:", err);
      setSummary("⚠️ Failed to generate summary.");
    }
    setLoading(false);
  };

  return (
    <div className="right-panel">
      {/* AI Analysis Section */}
      <h3>AI Analysis</h3>
      <div className="small">Credibility Engine</div>
      <div className="panel-block">
        <div className="panel-row">
          <div className="panel-title">
            Processing {(m.total_incidents || 240) / 2} reports/hour
          </div>
          <div className="panel-pill">Active</div>
        </div>

        <div className="accuracy-bar">
          <div className="accuracy-track">
            <div
              className="accuracy-fill"
              style={{ width: `${m.accuracy ?? 75}%` }}
            />
          </div>
          <div className="accuracy-caption">{(m.accuracy ?? 75)}% accuracy rate</div>
        </div>
      </div>

      {/* 🚀 Summary Generator */}
      <div className="panel-block">
        <h3>Summary Generator</h3>
        <div className="small">Paste news/article below to get a summary</div>

        {/* Input Box */}
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Enter or paste a long text here..."
          className="summary-input"
        />

        {/* Summarize Button */}
        <button
          onClick={handleSummarize}
          className="btn summary-button"
          disabled={loading}
        >
          {loading ? "Summarizing..." : "Generate Summary"}
        </button>

        {/* Output Box */}
        {summary && (
          <div className="summary-output">
            <small>{summary}</small>
          </div>
        )}
      </div>

      {/* Live Data Feed */}
      <div className="panel-block">
        <h3>Live Data Feed</h3>
        <div className="feed-list">
          {feed && feed.length > 0 ? (
            feed.map((item, idx) => (
              <div
                key={idx}
                className="feed-item"
              >
                <div className="feed-title">{item.title}</div>
                <div className="feed-summary">
                  {item.summary ||
                    item.description?.slice(0, 100) ||
                    "No details available"}
                </div>
                <div className="feed-meta">
                  {item.incident_type || "Unknown type"} •{" "}
                  {item.location_text || "Unknown location"}
                </div>
                {item.source_url && (
                  <a
                    href={item.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="feed-link"
                  >
                    Read more
                  </a>
                )}
              </div>
            ))
          ) : (
            <div className="empty-state">Waiting for live data...</div>
          )}
        </div>
      </div>

      {/* Performance Metrics */}
      <PerformanceMetrics
        metrics={{
          apiTime: m.apiTime ?? 142,
          accuracy: m.accuracy ?? 75,
          dataProcessing: m.dataProcessing ?? 76,
        }}
      />
    </div>
  );
}
