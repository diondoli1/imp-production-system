import React, { useState } from "react";

export default function LoginPage({ onLogin }) {
  const [name, setName] = useState("");
  const [pin, setPin] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");
    setSubmitting(true);
    try {
      await onLogin(name, pin);
    } catch (error) {
      setMessage(`Login failed: ${error.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page-grid">
      <section className="panel">
        <h3>Login</h3>
        <form className="form-row" onSubmit={handleSubmit}>
          <input
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoComplete="username"
            required
          />
          <input
            placeholder="PIN"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            type="password"
            autoComplete="current-password"
            required
          />
          <button type="submit" disabled={submitting}>
            {submitting ? "Signing In..." : "Sign In"}
          </button>
        </form>
        <p className="message">{message || "Use operator or supervisor credentials."}</p>
      </section>
    </div>
  );
}