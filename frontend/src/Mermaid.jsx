import { useEffect, useRef, useState } from "react";

// Lazy-load the (heavy) mermaid lib only when a diagram is actually rendered,
// so it stays out of the initial bundle.
let _mermaid = null;
async function getMermaid() {
  if (!_mermaid) {
    _mermaid = (await import("mermaid")).default;
    _mermaid.initialize({ startOnLoad: false, theme: "dark", securityLevel: "strict" });
  }
  return _mermaid;
}

let _id = 0;

// Renders a Mermaid string to SVG. On a syntax error, falls back to showing the
// raw source in a <pre> (never throws / crashes the page).
export default function Mermaid({ chart }) {
  const [svg, setSvg] = useState("");
  const [failed, setFailed] = useState(false);
  const idRef = useRef(`mmd-${_id++}`);

  useEffect(() => {
    let cancelled = false;
    const src = (chart || "").trim();
    if (!src) {
      setSvg("");
      setFailed(false);
      return;
    }
    getMermaid()
      .then((m) => m.render(idRef.current, src))
      .then(({ svg }) => {
        if (!cancelled) {
          setSvg(svg);
          setFailed(false);
        }
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [chart]);

  if (failed || !svg) {
    return <pre className="ref">{chart}</pre>;
  }
  return <div className="mermaid-svg" dangerouslySetInnerHTML={{ __html: svg }} />;
}
