"""Orchestration: generate a scenario, judge an answer, explode pattern gaps."""

import json

from fastapi import HTTPException
from sqlalchemy.orm import Session as DbSession

from . import llm, prompts
from .access import assert_owner
from .config import settings
from .models import (
    ExerciseType,
    JobStatus,
    PatternGap,
    Scenario,
    Session,
    StudyNote,
    StudyNoteKind,
    User,
)
from .schemas import ScenarioCreate, SessionCreate

# ---------------------------------------------------------------------------
# Async job model: enqueue_* creates a `pending` row and returns immediately;
# the worker thread (worker.py) later calls run_*_job to do the slow LLM call.
# ---------------------------------------------------------------------------


def _generate_json(system: str, user_prompt: str, model: str, attempts: int = 2) -> dict:
    """complete() + parse, regenerating once if the model emits unrepairable JSON.
    Cheap here because we're in the background worker, not a request."""
    last: HTTPException | None = None
    for _ in range(max(1, attempts)):
        raw = llm.complete(system, user_prompt, model=model)
        try:
            return llm.parse_model_json(raw)
        except HTTPException as exc:
            last = exc  # malformed JSON even after repair — try a fresh generation
    raise last  # type: ignore[misc]


def _gen_hint(db: DbSession, payload: ScenarioCreate, user: User) -> str | None:
    """Build an extra generation instruction from a harder-variation seed or a
    focus pattern (smart review)."""
    parts: list[str] = []
    if payload.focus_pattern:
        parts.append(
            "Design the exercise so a strong answer must apply and correctly name this "
            f"pattern/concept: {payload.focus_pattern}."
        )
    if payload.variation_of:
        parent = assert_owner(db.get(Scenario, payload.variation_of), user)
        parts.append(
            "Create a HARDER variation of this exercise — same topic and exercise type, higher "
            f"difficulty, a different concrete scenario: “{parent.title}” — {parent.problem}"
        )
    return "\n".join(parts) or None


def enqueue_scenario(db: DbSession, payload: ScenarioCreate, user: User) -> Scenario:
    """Create a pending scenario placeholder — no LLM call here."""
    gen_hint = _gen_hint(db, payload, user)
    scenario = Scenario(
        difficulty=payload.difficulty,
        focus_area=payload.focus_area,
        exercise_type=payload.exercise_type,
        language=payload.language,
        title="",
        context="",
        problem="",
        constraints=[],
        reference_solution={},
        response_template=[],
        model=payload.model or settings.llm_model,
        gen_hint=gen_hint,
        user_id=user.id,
        status=JobStatus.pending,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


def run_scenario_job(db: DbSession, scenario: Scenario) -> None:
    """Worker side: do the LLM generation and fill the row in place."""
    etype = scenario.exercise_type
    if etype == ExerciseType.language:
        # 'any' is meaningless for a language-specific gotcha — default to Python.
        lang = scenario.language if scenario.language and scenario.language != "any" else "Python"
        system = prompts.LANGUAGE_SYSTEM
        user_prompt = prompts.language_user_prompt(lang)
    elif etype == ExerciseType.algorithms:
        system = prompts.ALGORITHMS_SYSTEM
        user_prompt = prompts.algorithms_user_prompt(scenario.language or "any")
    else:
        system = prompts.SCENARIO_SYSTEM
        user_prompt = prompts.scenario_user_prompt(
            scenario.difficulty.value,
            scenario.focus_area,
            structured=(etype == ExerciseType.structured),
        )

    if scenario.gen_hint:
        user_prompt += f"\n\nAdditional instruction:\n{scenario.gen_hint}"

    data = _generate_json(system, user_prompt, scenario.model)
    missing = [k for k in ("title", "context", "problem", "reference_solution") if k not in data]
    if missing:
        raise HTTPException(
            status_code=502,
            detail=f"Model response is missing required field(s): {', '.join(missing)}.",
        )
    scenario.title = data["title"]
    scenario.context = data["context"]
    scenario.problem = data["problem"]
    scenario.constraints = data.get("constraints", [])
    scenario.reference_solution = data["reference_solution"]
    if etype == ExerciseType.structured:
        scenario.response_template = data.get("response_template", [])
        scenario.context_diagram = data.get("context_diagram") or None
    scenario.status = JobStatus.ready
    scenario.error = None
    db.commit()


def _scenario_block(scenario: Scenario) -> str:
    return (
        f"Title: {scenario.title}\n"
        f"Context: {scenario.context}\n"
        f"Problem: {scenario.problem}\n"
        f"Constraints:\n- " + "\n- ".join(scenario.constraints)
    )


def enqueue_session(db: DbSession, payload: SessionCreate, scenario: Scenario, user: User) -> Session:
    """Create a pending judging job — no LLM call here."""
    session = Session(
        scenario_id=scenario.id,
        user_answer=payload.user_answer,
        answer_freehand=payload.answer_freehand,  # stored, never judged
        run_id=payload.run_id,  # interview grouping (Phase D)
        judgment={},
        score=0,
        model=scenario.model,  # judge with the model that generated the scenario
        user_id=user.id,
        status=JobStatus.pending,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def run_session_job(db: DbSession, session: Session) -> None:
    """Worker side: judge the answer, fill the row, explode pattern gaps."""
    scenario = session.scenario
    etype = scenario.exercise_type
    judgment = _generate_json(
        prompts.JUDGE_SYSTEM,
        prompts.judge_user_prompt(
            _scenario_block(scenario),
            json.dumps(scenario.reference_solution, indent=2),
            session.user_answer,
            structured=(etype == ExerciseType.structured),
            requirements=list(scenario.constraints or []),
            exercise_type=etype.value,
        ),
        session.model,
    )
    session.judgment = judgment
    session.score = int(judgment.get("score_1_to_5") or 0)
    session.status = JobStatus.ready
    session.error = None

    for up in judgment.get("unnamed_patterns", []):
        db.add(
            PatternGap(
                session_id=session.id,
                pattern_name=up.get("pattern_name", "") or "(unnamed)",
                what_they_described=up.get("what_they_described", ""),
            )
        )
    db.commit()


def enqueue_study_note(
    db: DbSession, topic: str, kind: StudyNoteKind, model: str | None, user: User
) -> StudyNote:
    """Create a pending study-note job — no LLM call here."""
    note = StudyNote(
        kind=kind,
        topic=topic,
        content_md="",
        model=model or settings.llm_model,
        user_id=user.id,
        status=JobStatus.pending,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def run_study_note_job(db: DbSession, note: StudyNote) -> None:
    """Worker side: AI-generate the Markdown body and fill the row.

    Markdown output (not JSON), so this never goes through parse_model_json —
    robust even on small/free models.
    """
    if note.kind == StudyNoteKind.cheat_sheet:
        system, user_prompt = prompts.CHEATSHEET_SYSTEM, prompts.cheatsheet_user_prompt(note.topic)
    else:
        system, user_prompt = prompts.STUDY_SYSTEM, prompts.study_user_prompt(note.topic)

    note.content_md = llm.complete(system, user_prompt, model=note.model).strip()
    note.status = JobStatus.ready
    note.error = None
    db.commit()
