// Shared tab bar. `tabs` is [{ key, label, hidden? }]; the parent renders the
// active panel itself (so tab content stays lazy and colocated with its state).
export default function Tabs({ tabs, active, onChange }) {
  const visible = tabs.filter((t) => !t.hidden);
  return (
    <div className="tabs">
      {visible.map((t) => (
        <button
          key={t.key}
          className={`tab ${active === t.key ? "on" : ""}`}
          onClick={() => onChange(t.key)}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
