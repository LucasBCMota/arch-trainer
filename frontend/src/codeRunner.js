// Runs the user's code entirely in the browser (WASM sandbox) — zero server
// cost, no server-side security risk. Python via Pyodide (loaded from CDN),
// JavaScript natively. Runs in a Blob-based *classic* Web Worker so a runaway
// loop can be terminated and importScripts() is available for Pyodide.

const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js";

const WORKER_SRC = `
let pyReady = null;
function loadPy() {
  if (!pyReady) { importScripts("${PYODIDE}"); pyReady = loadPyodide(); }
  return pyReady;
}
function fmt(x){ try { return typeof x === "object" ? JSON.stringify(x) : String(x); } catch(_) { return String(x); } }
self.onmessage = async (e) => {
  const { language, code } = e.data;
  try {
    if (language === "python") {
      const py = await loadPy();
      let buf = "";
      py.setStdout({ batched: (s) => { buf += s; } });
      py.setStderr({ batched: (s) => { buf += s; } });
      self.postMessage({ phase: "running" });
      await py.runPythonAsync(code);
      self.postMessage({ done: true, stdout: buf });
    } else {
      let buf = "";
      const c = (...a) => { buf += a.map(fmt).join(" ") + "\\n"; };
      const cons = { log: c, error: c, warn: c, info: c, debug: c };
      self.postMessage({ phase: "running" });
      new Function("console", code)(cons);
      self.postMessage({ done: true, stdout: buf });
    }
  } catch (err) {
    self.postMessage({ done: true, error: String((err && err.message) || err) });
  }
};
`;

export function runnableLang(language) {
  const l = (language || "").toLowerCase();
  if (l.includes("python")) return "python";
  // plain JS only — TS type annotations won't run without transpilation
  if (l.includes("javascript") && !l.includes("typescript")) return "javascript";
  return null;
}

export function runCode(language, code, { execTimeoutMs = 6000, loadGuardMs = 45000 } = {}) {
  return new Promise((resolve) => {
    let worker;
    try {
      const url = URL.createObjectURL(new Blob([WORKER_SRC], { type: "application/javascript" }));
      worker = new Worker(url);
    } catch {
      resolve({ error: "Could not start the in-browser runner." });
      return;
    }
    // Guard the (possibly slow) first Pyodide load; swap to a tight execution
    // timeout once the code actually starts running.
    let timer = setTimeout(() => {
      worker.terminate();
      resolve({ error: "Timed out loading the runtime — check your connection and retry." });
    }, loadGuardMs);

    worker.onmessage = (e) => {
      const d = e.data;
      if (d.phase === "running") {
        clearTimeout(timer);
        timer = setTimeout(() => {
          worker.terminate();
          resolve({ error: `Timed out after ${execTimeoutMs / 1000}s (possible infinite loop).` });
        }, execTimeoutMs);
        return;
      }
      if (d.done) {
        clearTimeout(timer);
        worker.terminate();
        resolve({ stdout: d.stdout || "", error: d.error || null });
      }
    };
    worker.onerror = (err) => {
      clearTimeout(timer);
      worker.terminate();
      resolve({ error: String(err.message || "runner error") });
    };
    worker.postMessage({ language, code });
  });
}
