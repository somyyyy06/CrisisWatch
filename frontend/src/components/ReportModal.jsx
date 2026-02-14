// src/components/ReportModal.jsx
import React from "react";
import ReportForm from "./ReportForm";

export default function ReportModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="report-shell" onClick={(e) => e.stopPropagation()}>
        <div className="report-shell-head">
          <div>
            <p className="report-eyebrow">Incident intake</p>
            <h3>Report new incident</h3>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <ReportForm />
      </div>
    </div>
  );
}
