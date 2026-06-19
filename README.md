# Architecture Reasoning Trainer

A personal tool for practicing system-design / architecture reasoning. One AI call generates a
realistic scenario **and** a hidden reference solution; you write your own answer; a second AI call
judges it against the reference — specifically naming patterns you used but didn't name (e.g. you
describe "delete the row first, only insert if it was deleted" and it tells you that's
compare-and-delete / optimistic locking). Sessions are stored so you can track which named patterns
you keep missing.

## Stack
- **Backend:** FastAPI + SQLAlchemy + Postgres, Alembic migrations, deps via `uv`.
- **Frontend:** React (Vite), plain CSS. Built and served by the backend in production.
- **AI:** swappable provider — Anthropic (official SDK), or OpenAI / OpenRouter (OpenAI SDK).
- **Deploy:** Render Blueprint (`render.yaml`) — one web service + managed Postgres.

## Choosing a model
Set `LLM_MODEL` as `provider:model_id`, and set that provider's key:

| `LLM_MODEL`                              | Key needed            |
| ---------------------------------------- | --------------------- |
| `anthropic:claude-sonnet-4-6` (default)  | `ANTHROPIC_API_KEY`   |
| `openrouter:anthropic/claude-3.5-sonnet` | `OPENROUTER_API_KEY`  |
| `openai:gpt-4o`                          | `OPENAI_API_KEY`      |

Keys are read from **env only**, never stored in the database. `GET /api/models` reports which
providers are configured; the Setup screen's model dropdown lets you switch at runtime.

## Run locally (docker-compose: Postgres + API)
```bash
cp .env.example .env          # set LLM_MODEL + at least one provider key
docker compose up --build     # API on http://localhost:8000 (runs migrations on boot)
curl localhost:8000/api/models
```
The API also serves the built frontend at `:8000`. For live frontend development, run it separately:
```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173, proxies /api -> :8000
```

## Run the backend without Docker
```bash
cd backend
cp .env.example .env          # point DATABASE_URL at a local Postgres
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Deploy to Render
1. Push this repo to GitHub.
2. In Render: **New → Blueprint**, point it at the repo. It reads `render.yaml` and provisions the
   web service + a managed Postgres. `DATABASE_URL` is wired automatically.
3. On the web service, set these env vars in the dashboard (they're `sync: false` in the blueprint):
   - `LLM_MODEL` (e.g. `anthropic:claude-sonnet-4-6`)
   - `ANTHROPIC_API_KEY` (and/or `OPENAI_API_KEY`, `OPENROUTER_API_KEY`)
4. Deploy. Migrations run on container start; the app is served at the Render URL.

## API
| Method | Path                       | Purpose                                                        |
| ------ | -------------------------- | -------------------------------------------------------------- |
| POST   | `/api/scenarios`           | Generate scenario + hidden reference; returns scenario only    |
| GET    | `/api/scenarios/{id}`      | Fetch scenario (`?reveal=true` includes the reference)         |
| POST   | `/api/sessions`            | Judge an answer; returns judgment + reference                  |
| GET    | `/api/sessions`            | Session history (paginated)                                    |
| GET    | `/api/sessions/export`     | Markdown export of all sessions                                |
| GET    | `/api/stats/pattern-gaps`  | Recurring unnamed-pattern frequency                            |
| GET    | `/api/stats/summary`       | Total sessions + average score                                 |
| GET    | `/api/models`              | Configured providers + suggested models + current default     |

Single-user tool — no auth.
