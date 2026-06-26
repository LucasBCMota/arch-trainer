import { useMemo } from "react";
import { Excalidraw } from "@excalidraw/excalidraw";
// v0.17 bundles its CSS into the JS — no separate stylesheet import needed.

// Freehand sketch pad. Heavy dependency — only imported lazily where used.
// `onScene` receives the current scene to store (elements only; not judged) —
// the caller MUST keep it in a ref, never state, or onChange will loop-render.
// `viewMode` renders a read-only replay (for the result comparison).
export default function ExcalidrawCanvas({ initialData, onScene, viewMode = false, height = 420 }) {
  // Stable identity so Excalidraw doesn't re-init on every parent render.
  const initial = useMemo(
    () => (initialData ? { elements: initialData.elements || [] } : undefined),
    [initialData]
  );

  return (
    <div style={{ height, border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
      <Excalidraw
        theme="dark"
        viewModeEnabled={viewMode}
        initialData={initial}
        onChange={(elements) => onScene && onScene({ elements })}
      />
    </div>
  );
}
