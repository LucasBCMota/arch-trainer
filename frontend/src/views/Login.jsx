import { useState } from "react";
import { api } from "../api.js";

export default function Login({ onAuthed }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.login(password);
      onAuthed();
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  return (
    <div className="panel" style={{ marginTop: 40 }}>
      <h2>Restricted</h2>
      <p className="muted" style={{ marginTop: -6 }}>
        Practice system-design reasoning against an AI-generated reference solution, and find the
        patterns you use but don't name. This instance is private — it spends real model tokens, so
        it's behind a password.
      </p>
      <form onSubmit={submit} className="row" style={{ marginTop: 18 }}>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          autoFocus
          style={{
            flex: 1,
            minWidth: 200,
            background: "var(--panel-2)",
            border: "1px solid var(--border)",
            color: "var(--text)",
            borderRadius: 6,
            padding: "10px 12px",
            font: "inherit",
          }}
        />
        <button className="primary" type="submit" disabled={loading || !password}>
          {loading ? "…" : "Enter"}
        </button>
      </form>
      {error && <p className="error" style={{ marginTop: 12 }}>{error}</p>}
    </div>
  );
}
