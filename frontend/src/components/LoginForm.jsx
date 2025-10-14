// src/components/LoginForm.jsx
import React from "react";
import AuthForm from "./AuthForm";

export default function LoginForm({ onLogin }) {
  return <AuthForm initialMode="login" onAuth={onLogin} />;
}
