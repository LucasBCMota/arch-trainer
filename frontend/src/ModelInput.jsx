import { useEffect, useState } from "react";
import { api } from "./api.js";

const LS_KEY = "arch.model";

// Remembers the chosen model string across views/reloads so you can switch on the
// fly without retyping. Empty string = use the server default (LLM_MODEL).
export function useModelSelection() {
  const [model, setModel] = useState(() => localStorage.getItem(LS_KEY) || "");
  const set = (v) => {
    setModel(v);
    if (v) localStorage.setItem(LS_KEY, v);
    else localStorage.removeItem(LS_KEY);
  };
  return [model, set];
}

// Free-text model entry with favorites (saved to your account) + suggestions.
// Type any OpenRouter slug, ★ it to save, or click a favorite to apply it.
export default function ModelInput({ value, onChange }) {
  const [models, setModels] = useState(null);
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    api.models().then(setModels).catch(() => {});
    api
      .me()
      .then((m) => {
        const favs = m.user?.favorite_models || [];
        setFavorites(favs);
        // Default to the top favorite if nothing is selected yet.
        if (!localStorage.getItem(LS_KEY) && favs.length) onChange(favs[0]);
      })
      .catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const suggestions = models
    ? Object.entries(models.suggested).flatMap(([prov, ids]) => ids.map((id) => `${prov}:${id}`))
    : [];
  const datalistOptions = [...new Set([...favorites, ...suggestions])];

  const trimmed = (value || "").trim();
  const isFav = favorites.includes(trimmed);

  async function toggleFav() {
    if (!trimmed) return;
    const next = isFav ? favorites.filter((m) => m !== trimmed) : [trimmed, ...favorites];
    setFavorites(next); // optimistic
    try {
      const res = await api.setFavoriteModels(next);
      setFavorites(res.favorite_models);
    } catch {
      setFavorites(favorites); // revert
    }
  }

  return (
    <>
      <div className="row" style={{ alignItems: "stretch" }}>
        <input
          className="text-input"
          list="model-suggestions"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={models ? `default: ${models.current} — or type provider:model` : "provider:model_id"}
          spellCheck={false}
          autoCapitalize="off"
          autoCorrect="off"
        />
        <button
          type="button"
          className="ghost"
          onClick={toggleFav}
          disabled={!trimmed}
          title={isFav ? "Remove from favorites" : "Save as favorite"}
        >
          {isFav ? "★" : "☆"}
        </button>
      </div>
      <datalist id="model-suggestions">
        {datalistOptions.map((m) => (
          <option key={m} value={m} />
        ))}
      </datalist>

      {favorites.length > 0 && (
        <div className="chips" style={{ marginTop: 8 }}>
          {favorites.map((m) => (
            <button
              key={m}
              type="button"
              className={`chip ${trimmed === m ? "on" : ""}`}
              onClick={() => onChange(m)}
              title="Use this model"
            >
              ★ {m}
            </button>
          ))}
        </div>
      )}
    </>
  );
}
