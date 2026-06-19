# Architecture Reasoning Trainer — Build Spec

## What this is
A personal tool for practicing system-design / architecture reasoning. The AI generates a
realistic scenario AND a hidden reference solution in the same call (so the reference is never
biased by my answer). I write my own solution. A second AI call judges my answer against the
reference, specifically calling out patterns I used but didn't name correctly (e.g. I describe
"delete the row first, only insert if it was deleted" and it should tell me that's optimistic
locking / compare-and-delete). Sessions are stored so I can track which named patterns I keep
missing over time.

## Stack
- Backend: FastAPI + SQLAlchemy + Postgres (Alembic for migrations), dependencies managed with
  `uv` (not pip/poetry) — same as the biofam project.
- Frontend: React (Vite), plain CSS or minimal Tailwind — keep it simple, this is a personal tool
- Deploy target: Render (API as a Render web service, Postgres as Render managed Postgres),
  same general setup as the biofam project. Include a render.yaml (Blueprint) so both the web
  service and the database are defined as infra-as-code rather than clicked together manually.
- Local dev: docker-compose with postgres + api, frontend run separately via `npm run dev`
- AI: Anthropic API (claude-sonnet-4-6 model string), called server-side only — never expose the
  API key to the frontend. Read key from env var ANTHROPIC_API_KEY.

## Data model
- `scenarios` table: id, created_at, difficulty (enum: feature/platform/principal), focus_area,
  title, context, problem, constraints (JSON array), reference_solution (JSON — see shape below)
- `sessions` table: id, scenario_id (FK), created_at, user_answer (text), judgment (JSON — see
  shape below), score (int 1-5)
- `pattern_gaps` table: id, session_id (FK), pattern_name (text), what_they_described (text) —
  one row per unnamed pattern flagged in a judgment, so this is directly queryable/aggregable
  without re-parsing JSON blobs every time.

This is a single-user personal tool — no auth/multi-tenancy needed for v1.

## API endpoints
- `POST /api/scenarios` — body: {difficulty, focus_area}. Calls Claude to generate scenario +
  reference_solution together, persists to `scenarios`, returns the scenario WITHOUT the
  reference_solution field (frontend must never see it before judging).
- `GET /api/scenarios/{id}` — fetch a scenario (still without reference, unless ?reveal=true,
  used after judging to show the full reference on the result screen).
- `POST /api/sessions` — body: {scenario_id, user_answer}. Loads the scenario's stored
  reference_solution server-side, calls Claude to judge, persists session + explodes
  unnamed_patterns into `pattern_gaps` rows, returns the full judgment + reference_solution.
- `GET /api/sessions` — list session history (paginated), for the dashboard.
- `GET /api/stats/pattern-gaps` — GROUP BY pattern_name, COUNT(*), ORDER BY count DESC — powers
  the "your recurring gaps" view.
- `GET /api/sessions/export` — returns a markdown file of all sessions (same export format as
  before: scenario, user answer, reference, missed points, unnamed patterns).

## Claude prompts to reuse (already validated, keep behavior identical)

### Scenario generation system prompt:
"You are a principal engineer designing a system-design exercise. You produce two things: a
realistic scenario, and a hidden reference solution. Be concrete and specific — invent a
real-sounding product/system, not abstract placeholders. Output ONLY valid JSON, no markdown
fences, no preamble."

### Scenario generation user prompt template:
Includes difficulty calibration text:
- feature-level: a bounded change to one service. Tests whether obvious constraints are caught.
- platform-level: touches other teams/services, external contracts, data ownership across
  boundaries.
- principal-level: org-wide implications, migration/rollout strategy, irreversible decisions,
  multi-year tradeoffs.

Requests JSON shape:
```json
{
  "title": "short scenario title",
  "context": "2-4 sentences of system/business context",
  "problem": "the specific problem or feature request, written like a real ticket or PM ask",
  "constraints": ["list", "of", "given constraints or non-functional requirements"],
  "reference_solution": {
    "summary": "2-3 sentence summary of the recommended approach",
    "key_decisions": [
      {"decision": "...", "pattern_name": "formal pattern name or null", "rationale": "why this over alternatives"}
    ],
    "tradeoffs_considered": ["alternative approach and why it was rejected"],
    "failure_modes_addressed": ["specific failure mode and how the design handles it"],
    "open_questions_for_pm": ["questions a senior engineer would still ask"]
  }
}
```

### Judging system prompt:
"You are a principal engineer judging a candidate's architectural reasoning against a
known-correct reference solution. Be honest and specific — this is for skill-building, not
encouragement. Identify exactly which named patterns the candidate's answer demonstrates but
failed to name, where their reasoning matched the reference, and where it genuinely diverged or
fell short. Do not be harsh for its own sake, but do not soften real gaps. Output ONLY valid
JSON, no markdown fences."

### Judging user prompt: 
Includes the scenario, the reference_solution (ground truth), and the candidate's answer.
Requests JSON shape:
```json
{
  "overall_assessment": "feature-level | platform-level | principal-level",
  "matched_points": ["..."],
  "missed_points": ["..."],
  "unnamed_patterns": [{"what_they_described": "...", "pattern_name": "..."}],
  "genuine_disagreements": ["cases where candidate's approach is defensible, not wrong"],
  "communication_gaps": ["reasoning was present but not clearly justified"],
  "score_1_to_5": 0,
  "one_line_verdict": "single direct sentence"
}
```

IMPORTANT: wrap the actual Claude API call in JSON-fence stripping + try/catch, since the model
sometimes wraps JSON in ```json fences despite instructions.

## Frontend views (already designed, port this UX)
1. **Setup** — chip selectors for difficulty (feature/platform/principal) and focus area
   (any/concurrency/external boundaries/data modeling/failure modes/scaling/consistency). Shows
   top recurring gaps if any exist. "Generate scenario" button.
2. **Answering** — shows scenario (title, context, problem, constraints) and a textarea for the
   free-text answer. "Submit for judgment" button.
3. **Result** — score badge (1-5), one-line verdict, then sections: Matched the reference /
   You did this but didn't name it (unnamed patterns, the most important section) / Missed
   entirely / Communication gaps / Defensible alternatives. Collapsible "full reference solution"
   at the bottom. Buttons: "Next scenario", "Export all sessions".
4. **Dashboard** — total sessions, average score, table of recurring unnamed-pattern frequency
   (this is the "what am I weak on" view — query pattern_gaps GROUP BY), session log list.

Visual style: dark background, IBM Plex Sans/Mono fonts, blue accent (~#3B5BFF), feels like a
technical instrument not a marketing page. Color-code score badges (green ≥4, yellow 3, red <3).
Color-code result sections (green=matched, yellow=unnamed patterns, red=missed).

## Env vars needed
- ANTHROPIC_API_KEY (backend only)
- DATABASE_URL (postgres connection string)

## Project conventions
A `CLAUDE.md` file is included in this repo (same format used in the biofam project) — it covers
the `.claude.md` memory-file system, commit message rules (single-line conventional commits, no
co-author trailers, no "Generated with Claude Code" footer). Follow it from the first commit.

## What I want from you (Claude Code)
1. Scaffold the full repo structure with backend + frontend + docker-compose + Alembic migration
   for the initial schema.
2. Implement the endpoints above, with the Claude API calls server-side.
3. Build the frontend views, wired to the real API instead of any local storage.
4. Get it running locally via docker-compose so I can test the full loop (generate → answer →
   judge → see in dashboard).
5. Add a render.yaml so it's deployable to Render with minimal extra config (web service +
   managed Postgres defined as a Blueprint) — tell me what env vars / steps I'll need to set in
   the Render dashboard.
6. Keep it simple. This is a personal tool for one user. Don't add auth, multi-tenancy, or
   infra complexity beyond what's specified here.

Ask me clarifying questions before generating a large volume of code if anything above is
ambiguous — otherwise proceed.
