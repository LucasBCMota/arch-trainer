import { useEffect, useState } from "react";
import { api } from "./api.js";
import Setup from "./views/Setup.jsx";
import Answering from "./views/Answering.jsx";
import Result from "./views/Result.jsx";
import Dashboard from "./views/Dashboard.jsx";
import Study from "./views/Study.jsx";
import Artifacts from "./views/Artifacts.jsx";
import Public from "./views/Public.jsx";
import Login from "./views/Login.jsx";

export default function App() {
  const [user, setUser] = useState(undefined); // undefined = loading, null = logged out
  const [view, setView] = useState("setup");
  const [scenario, setScenario] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api
      .me()
      .then((m) => setUser(m.authenticated ? m.user : null))
      .catch(() => setUser(null));
  }, []);

  const isOwner = !!user?.is_owner;

  function startAnswering(sc) {
    setScenario(sc);
    setView("answering");
  }
  function showResult(res) {
    setResult(res);
    setView("result");
  }
  function reset() {
    setScenario(null);
    setResult(null);
    setView("setup");
  }

  return (
    <div className="app">
      <header className="top">
        <h1>
          architecture<span className="dot">.</span>trainer
        </h1>
        {user && (
          <nav>
            <button className={["setup", "answering", "result"].includes(view) ? "active" : ""} onClick={reset}>
              train
            </button>
            <button className={view === "study" ? "active" : ""} onClick={() => setView("study")}>
              study
            </button>
            <button className={view === "artifacts" ? "active" : ""} onClick={() => setView("artifacts")}>
              artifacts
            </button>
            <button className={view === "public" ? "active" : ""} onClick={() => setView("public")}>
              public
            </button>
            <button className={view === "dashboard" ? "active" : ""} onClick={() => setView("dashboard")}>
              dashboard
            </button>
            <button onClick={() => (window.location.href = api.logoutUrl)} title={user.email}>
              logout
            </button>
          </nav>
        )}
      </header>

      {user === undefined && <p className="muted">Loading…</p>}
      {user === null && <Login />}

      {user && (
        <>
          {!isOwner && (view === "setup" || view === "study" || view === "artifacts") && (
            <p className="muted" style={{ fontSize: 13 }}>
              You're signed in as a viewer — AI generation is owner-only (it spends the host's LLM
              keys). You can browse <b>public</b> artifacts and import your own pasted notes.
            </p>
          )}
          {view === "setup" && <Setup onScenario={startAnswering} isOwner={isOwner} />}
          {view === "answering" && (
            <Answering scenario={scenario} onResult={showResult} onCancel={reset} isOwner={isOwner} />
          )}
          {view === "result" && (
            <Result
              scenario={scenario}
              result={result}
              onNext={reset}
              onScenario={startAnswering}
              isOwner={isOwner}
            />
          )}
          {view === "study" && <Study isOwner={isOwner} />}
          {view === "artifacts" && <Artifacts isOwner={isOwner} />}
          {view === "public" && <Public />}
          {view === "dashboard" && <Dashboard />}
        </>
      )}
    </div>
  );
}
