// src/components/AuthForm.jsx
import React, { useState, useEffect } from "react";
import { API_BASE } from "../config/api";

export default function AuthForm({ initialMode = "login", mode: controlledMode, onModeChange, onAuth }) {
  const [mode, setMode] = useState(initialMode);
  const activeMode = controlledMode ?? mode;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (controlledMode == null) {
      setMode(initialMode || "login");
    }
  }, [initialMode, controlledMode]);

  const changeMode = (nextMode) => {
    if (onModeChange) onModeChange(nextMode);
    if (controlledMode == null) setMode(nextMode);
  };

  const doLogin = async (emailArg = email, passwordArg = password) => {
    setLoading(true);
    setStatus("Logging in...");
    try {
      const form = new URLSearchParams();
      form.append("username", emailArg);
      form.append("password", passwordArg);

      const resp = await fetch(`${API_BASE}/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form,
      });

      if (!resp.ok) {
        const text = await resp.text();
        setStatus("Login failed: " + (text || resp.status));
        setLoading(false);
        return false;
      }

      const data = await resp.json();
      localStorage.setItem("token", data.access_token);
      setStatus("Login successful!");
      try {
        window.dispatchEvent(new Event("storage"));
      } catch {}
      if (onAuth) onAuth();
      setLoading(false);
      return true;
    } catch (err) {
      setStatus("Error: " + err.message);
      setLoading(false);
      return false;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("");
    if (!email || !password) {
      setStatus("Please fill email and password.");
      return;
    }

    if (activeMode === "signup") {
      setLoading(true);
      setStatus("Signing up...");
      try {
        // ✅ FIXED: use /auth/signup instead of /auth/register
        const resp = await fetch(`${API_BASE}/auth/signup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: email, email, password }),
        });

        if (!resp.ok) {
          const err = await resp.json().catch(() => null);
          const message =
            err?.detail || "Signup failed: " + resp.statusText || resp.status;
          setStatus(message);
          setLoading(false);
          return;
        }

        setStatus("Signup successful — logging in...");
        const ok = await doLogin(email, password);
        if (!ok) {
          setStatus("Signed up, but auto-login failed. Please login.");
        }
      } catch (err) {
        setStatus("Error: " + err.message);
        setLoading(false);
      } finally {
        setLoading(false);
      }
    } else {
      await doLogin();
    }
  };

  function handleLogout() {
    localStorage.removeItem("token");
    setStatus("Logged out.");
    try {
      window.dispatchEvent(new Event("storage"));
    } catch {}
    if (onAuth) onAuth();
  }

  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  if (token) {
    return (
      <div className="auth-card auth-signed-in">
        <div>
          <p className="auth-signed-title">You are signed in</p>
          <p className="auth-signed-sub">Access confirmed. You can report incidents and manage alerts.</p>
        </div>
        <div className="auth-actions">
          <button className="btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
        {status ? <div className="auth-status">{status}</div> : null}
      </div>
    );
  }

  return (
    <div className="auth-card">
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="auth-field">
          <label>Email address</label>
          <input
            className="auth-input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@agency.org"
            required
          />
        </div>

        <div className="auth-field">
          <label>Password</label>
          <input
            className="auth-input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Minimum 4 characters"
            required
          />
        </div>

        <div className="auth-actions">
          <button className="btn" type="submit" disabled={loading}>
            {activeMode === "login"
              ? loading
                ? "Signing in..."
                : "Sign In"
              : loading
              ? "Signing up..."
              : "Create account"}
          </button>
        </div>
      </form>

      <div className="auth-switch">
        {activeMode === "login" ? (
          <p>
            New here?{" "}
            <button type="button" onClick={() => changeMode("signup")}>
              Create an account
            </button>
          </p>
        ) : (
          <p>
            Already registered?{" "}
            <button type="button" onClick={() => changeMode("login")}>
              Sign in instead
            </button>
          </p>
        )}
      </div>

      {status ? <div className="auth-status">{status}</div> : null}
    </div>
  );
}