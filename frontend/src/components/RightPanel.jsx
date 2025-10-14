// src/components/RightPanel.jsx
import React, { useState } from "react";
import PerformanceMetrics from "./PerformanceMetrics";

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
      const response = await fetch("http://127.0.0.1:8000/summarize", {
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
    <div>
      {/* AI Analysis Section */}
      <h3>AI Analysis</h3>
      <div className="small">Credibility Engine</div>
      <div style={{ marginTop: 8 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div style={{ fontWeight: 700 }}>
            Processing {(m.total_incidents || 240) / 2} reports/hour
          </div>
          <div style={{ color: "#39b54a", fontSize: 13 }}>Active</div>
        </div>

        {/* Accuracy Bar */}
        <div style={{ marginTop: 10 }}>
          <div
            style={{
              height: 10,
              background: "rgba(255,255,255,0.05)",
              borderRadius: 8,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${m.accuracy ?? 75}%`,
                height: "100%",
                background: "linear-gradient(90deg,#2F80ED,#2AA7FF)",
              }}
            />
          </div>
        </div>
        <div style={{ marginTop: 8, fontSize: 13, color: "#9aa7bf" }}>
          {(m.accuracy ?? 75)}% accuracy rate
        </div>
      </div>

      {/* 🚀 Summary Generator */}
      <div style={{ marginTop: 18 }}>
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
          className="btn"
          style={{ marginTop: 8 }}
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
      <div style={{ marginTop: 18 }}>
        <h3>Live Data Feed</h3>
        <div
          className="feed-list"
          style={{ marginTop: 8, maxHeight: 300, overflowY: "auto" }}
        >
          {feed && feed.length > 0 ? (
            feed.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: "8px 0",
                  borderBottom: "1px solid rgba(255,255,255,0.05)",
                }}
              >
                <div style={{ fontWeight: 600 }}>{item.title}</div>
                <div
                  style={{ fontSize: 13, color: "#9aa7bf", marginTop: 2 }}
                >
                  {item.summary ||
                    item.description?.slice(0, 100) ||
                    "No details available"}
                </div>
                <div style={{ fontSize: 12, color: "#aaa", marginTop: 4 }}>
                  {item.incident_type || "Unknown type"} •{" "}
                  {item.location_text || "Unknown location"}
                </div>
                {item.source_url && (
                  <a
                    href={item.source_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ fontSize: 12, color: "#2AA7FF" }}
                  >
                    Read more
                  </a>
                )}
              </div>
            ))
          ) : (
            <div className="small" style={{ color: "#9aa7bf" }}>
              Waiting for live data...
            </div>
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
