// src/components/AuthModal.jsx
import React from "react";
import AuthForm from "./AuthForm"; // your existing AuthForm (we already improved it earlier)

export default function AuthModal({ isOpen, onClose, initialMode = "login", onAuth }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="auth-shell" onClick={(e) => e.stopPropagation()}>
        <div className="auth-visual">
          <div className="auth-brand">CW</div>
          <h3 className="auth-visual-title">CrisisWatch Access</h3>
          <p className="auth-visual-sub">
            Real-time incident signals, verified at speed. Secure your workspace to report and track events.
          </p>
          <div className="auth-visual-tags">
            <span>Live reports</span>
            <span>Trust scoring</span>
            <span>Location aware</span>
          </div>
        </div>

        <div className="auth-panel">
          <div className="auth-panel-head">
            <div>
              <p className="auth-eyebrow">Welcome back</p>
              <h3 className="auth-title">{initialMode === "login" ? "Sign In" : "Create account"}</h3>
            </div>
            <button className="modal-close" onClick={onClose}>✕</button>
          </div>

          <AuthForm
            initialMode={initialMode}
            onAuth={() => {
              if (onAuth) onAuth();
              onClose();
            }}
          />
        </div>
      </div>
    </div>
  );
}
