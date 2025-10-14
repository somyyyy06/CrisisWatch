// src/components/ReportModal.jsx
import React from "react";
import ReportForm from "./ReportForm";

export default function ReportModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Report New Incident</h3>
          <button className="close" onClick={onClose}>✕</button>
        </div>

        <div style={{ marginBottom: 12 }}>
          {/* Reuse your existing ReportForm component */}
          <ReportForm />
        </div>

        <div style={{ textAlign: "right" }}>
          <button className="btn ghost" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
