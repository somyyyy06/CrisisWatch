// src/components/AuthForm.jsx
import React, { useState, useEffect } from "react";

const API = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function AuthForm({ initialMode = "login", onAuth }) {
  const [mode, setMode] = useState(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setMode(initialMode || "login");
  }, [initialMode]);

  const doLogin = async (emailArg = email, passwordArg = password) => {
    setLoading(true);
    setStatus("Logging in...");
    try {
      const form = new URLSearchParams();
      form.append("username", emailArg);
      form.append("password", passwordArg);

      const resp = await fetch(`${API}/auth/token`, {
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

    if (mode === "signup") {
      setLoading(true);
      setStatus("Signing up...");
      try {
        // ✅ FIXED: use /auth/signup instead of /auth/register
        const resp = await fetch(`${API}/auth/signup`, {
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
      <div className="auth-modal">
        <p>✅ You are signed in.</p>
        <div className="auth-actions">
          <button className="btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
        <div className="auth-status">{status}</div>
      </div>
    );
  }

  return (
    <div className="auth-modal">
      <h3>{mode === "login" ? "Sign In" : "Sign Up"}</h3>

      <form className="auth-form" onSubmit={handleSubmit}>
        <div>
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div>
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <div className="auth-actions">
          <button className="btn" type="submit" disabled={loading}>
            {mode === "login"
              ? loading
                ? "Signing in..."
                : "Sign In"
              : loading
              ? "Signing up..."
              : "Sign Up"}
          </button>
        </div>
      </form>

      <div className="auth-switch">
        {mode === "login" ? (
          <p>
            No account?{" "}
            <button type="button" onClick={() => setMode("signup")}>
              Signup here
            </button>
          </p>
        ) : (
          <p>
            Already have an account?{" "}
            <button type="button" onClick={() => setMode("login")}>
              Login here
            </button>
          </p>
        )}
      </div>

      <div className="auth-status">{status}</div>
    </div>
  );
}