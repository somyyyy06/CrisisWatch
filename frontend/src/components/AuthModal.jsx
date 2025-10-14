// src/components/AuthModal.jsx
import React from "react";
import AuthForm from "./AuthForm"; // your existing AuthForm (we already improved it earlier)

export default function AuthModal({ isOpen, onClose, initialMode = "login", onAuth }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ margin: 0 }}>{initialMode === "login" ? "Sign In" : "Sign Up"}</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div style={{ marginTop: 12 }}>
          <AuthForm initialMode={initialMode} onAuth={() => { if (onAuth) onAuth(); onClose(); }} />
        </div>
      </div>
    </div>
  );
}
