import { useState } from "react";
import Setup from "./views/Setup.jsx";
import Answering from "./views/Answering.jsx";
import Result from "./views/Result.jsx";
import Dashboard from "./views/Dashboard.jsx";

export default function App() {
  const [view, setView] = useState("setup");
  const [scenario, setScenario] = useState(null);
  const [result, setResult] = useState(null);

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
        <nav>
          <button
            className={view === "setup" || view === "answering" || view === "result" ? "active" : ""}
            onClick={reset}
          >
            train
          </button>
          <button className={view === "dashboard" ? "active" : ""} onClick={() => setView("dashboard")}>
            dashboard
          </button>
        </nav>
      </header>

      {view === "setup" && <Setup onScenario={startAnswering} />}
      {view === "answering" && (
        <Answering scenario={scenario} onResult={showResult} onCancel={reset} />
      )}
      {view === "result" && (
        <Result scenario={scenario} result={result} onNext={reset} />
      )}
      {view === "dashboard" && <Dashboard />}
    </div>
  );
}
