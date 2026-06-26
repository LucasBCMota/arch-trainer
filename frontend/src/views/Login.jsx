import { api } from "../api.js";

export default function Login() {
  return (
    <div className="panel" style={{ marginTop: 40 }}>
      <h2>Architecture Trainer</h2>
      <p className="muted" style={{ marginTop: -6 }}>
        Practice system-design reasoning against an AI-generated reference solution, find the patterns
        you use but don't name, and build a study library. Sign in to start.
      </p>
      <div className="row" style={{ marginTop: 18 }}>
        <button className="primary" onClick={() => (window.location.href = api.loginUrl)}>
          Log in
        </button>
        <button className="ghost" onClick={() => (window.location.href = api.googleLoginUrl)}>
          Continue with Google
        </button>
      </div>
    </div>
  );
}
