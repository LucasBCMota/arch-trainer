"""Orchestration: generate a scenario, judge an answer, explode pattern gaps."""

import json

from sqlalchemy.orm import Session as DbSession

from . import llm, prompts
from .config import settings
from .models import PatternGap, Scenario, Session, StudyNote, StudyNoteKind
from .schemas import ScenarioCreate, SessionCreate


def generate_scenario(db: DbSession, payload: ScenarioCreate) -> Scenario:
    model = payload.model or settings.llm_model
    raw = llm.complete(
        prompts.SCENARIO_SYSTEM,
        prompts.scenario_user_prompt(payload.difficulty.value, payload.focus_area),
        model=model,
    )
    data = llm.parse_model_json(raw)

    scenario = Scenario(
        difficulty=payload.difficulty,
        focus_area=payload.focus_area,
        title=data["title"],
        context=data["context"],
        problem=data["problem"],
        constraints=data.get("constraints", []),
        reference_solution=data["reference_solution"],
        model=model,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


def _scenario_block(scenario: Scenario) -> str:
    return (
        f"Title: {scenario.title}\n"
        f"Context: {scenario.context}\n"
        f"Problem: {scenario.problem}\n"
        f"Constraints:\n- " + "\n- ".join(scenario.constraints)
    )


def judge_answer(db: DbSession, payload: SessionCreate, scenario: Scenario) -> Session:
    """Load the stored reference server-side, judge, persist, explode pattern gaps."""
    model = scenario.model  # judge with the model that generated the scenario
    raw = llm.complete(
        prompts.JUDGE_SYSTEM,
        prompts.judge_user_prompt(
            _scenario_block(scenario),
            json.dumps(scenario.reference_solution, indent=2),
            payload.user_answer,
        ),
        model=model,
    )
    judgment = llm.parse_model_json(raw)

    score = int(judgment.get("score_1_to_5") or 0)
    session = Session(
        scenario_id=scenario.id,
        user_answer=payload.user_answer,
        judgment=judgment,
        score=score,
        model=model,
    )
    db.add(session)
    db.flush()  # assign session.id before creating child rows

    for up in judgment.get("unnamed_patterns", []):
        db.add(
            PatternGap(
                session_id=session.id,
                pattern_name=up.get("pattern_name", "") or "(unnamed)",
                what_they_described=up.get("what_they_described", ""),
            )
        )

    db.commit()
    db.refresh(session)
    return session


def generate_study_note(
    db: DbSession, topic: str, kind: StudyNoteKind, model: str | None
) -> StudyNote:
    """AI-generate a Markdown study note or cheat-sheet and store it.

    Markdown output (not JSON), so this never goes through parse_model_json —
    robust even on small/free models.
    """
    model = model or settings.llm_model
    if kind == StudyNoteKind.cheat_sheet:
        system, user = prompts.CHEATSHEET_SYSTEM, prompts.cheatsheet_user_prompt(topic)
    else:
        system, user = prompts.STUDY_SYSTEM, prompts.study_user_prompt(topic)

    content = llm.complete(system, user, model=model).strip()
    note = StudyNote(kind=kind, topic=topic, content_md=content, model=model)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
