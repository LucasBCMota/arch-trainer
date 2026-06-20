import { useEffect, useState } from "react";
import { api } from "./api.js";
import Setup from "./views/Setup.jsx";
import Answering from "./views/Answering.jsx";
import Result from "./views/Result.jsx";
import Dashboard from "./views/Dashboard.jsx";
import Study from "./views/Study.jsx";
import Artifacts from "./views/Artifacts.jsx";
import Login from "./views/Login.jsx";

export default function App() {
  const [auth, setAuth] = useState(null); // null = unknown, false = needs login, true = ok
  const [view, setView] = useState("setup");
  const [scenario, setScenario] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api
      .me()
      .then((m) => setAuth(m.authenticated))
      .catch(() => setAuth(false));
  }, []);

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
  async function logout() {
    await api.logout().catch(() => {});
    setAuth(false);
    reset();
  }

  return (
    <div className="app">
      <header className="top">
        <h1>
          architecture<span className="dot">.</span>trainer
        </h1>
        {auth && (
          <nav>
            <button
              className={["setup", "answering", "result"].includes(view) ? "active" : ""}
              onClick={reset}
            >
              train
            </button>
            <button className={view === "study" ? "active" : ""} onClick={() => setView("study")}>
              study
            </button>
            <button className={view === "artifacts" ? "active" : ""} onClick={() => setView("artifacts")}>
              artifacts
            </button>
            <button className={view === "dashboard" ? "active" : ""} onClick={() => setView("dashboard")}>
              dashboard
            </button>
            <button onClick={logout}>logout</button>
          </nav>
        )}
      </header>

      {auth === null && <p className="muted">Loading…</p>}
      {auth === false && <Login onAuthed={() => setAuth(true)} />}

      {auth && (
        <>
          {view === "setup" && <Setup onScenario={startAnswering} />}
          {view === "answering" && (
            <Answering scenario={scenario} onResult={showResult} onCancel={reset} />
          )}
          {view === "result" && <Result scenario={scenario} result={result} onNext={reset} />}
          {view === "study" && <Study />}
          {view === "artifacts" && <Artifacts />}
          {view === "dashboard" && <Dashboard />}
        </>
      )}
    </div>
  );
}
