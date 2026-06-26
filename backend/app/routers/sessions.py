import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from .. import services
from ..access import assert_owner
from ..auth import current_user, require_owner
from ..db import get_db
from ..models import Scenario, Session, User
from ..schemas import SessionCreate, SessionOut, SessionResult, VisibilityBody

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionResult)
def create_session(
    payload: SessionCreate,
    db: DbSession = Depends(get_db),
    owner: User = Depends(require_owner),  # judging spends the server's keys
) -> SessionResult:
    # You may only answer your own scenario (assert_owner → 404 otherwise).
    scenario = assert_owner(db.get(Scenario, payload.scenario_id), owner)
    session = services.judge_answer(db, payload, scenario, owner)
    base = SessionOut.model_validate(session)
    return SessionResult(**base.model_dump(), reference_solution=scenario.reference_solution)


@router.get("", response_model=list[SessionOut])
def list_sessions(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user),
) -> list[Session]:
    stmt = (
        select(Session)
        .where(Session.user_id == user.id)  # your own history only
        .order_by(Session.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


@router.post("/{session_id}/visibility", response_model=SessionOut)
def set_visibility(
    session_id: uuid.UUID,
    payload: VisibilityBody,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user),
) -> Session:
    session = assert_owner(db.get(Session, session_id), user)
    session.visibility = payload.visibility
    db.commit()
    db.refresh(session)
    return session


@router.get("/export", response_class=PlainTextResponse)
def export_sessions(
    db: DbSession = Depends(get_db), user: User = Depends(current_user)
) -> PlainTextResponse:
    stmt = (
        select(Session)
        .where(Session.user_id == user.id)
        .order_by(Session.created_at.asc())
    )
    sessions = list(db.scalars(stmt).all())

    lines: list[str] = ["# Architecture Trainer — Session Export\n"]
    for s in sessions:
        sc = s.scenario
        j = s.judgment or {}
        lines.append(f"## {sc.title}  (score {s.score}/5)")
        lines.append(f"_{s.created_at:%Y-%m-%d %H:%M} · {sc.difficulty.value} · {sc.focus_area} · {s.model}_\n")
        lines.append(f"**Problem:** {sc.problem}\n")
        lines.append("### My answer")
        lines.append(s.user_answer + "\n")
        lines.append("### Verdict")
        lines.append(j.get("one_line_verdict", "") + "\n")

        missed = j.get("missed_points", [])
        if missed:
            lines.append("### Missed points")
            lines.extend(f"- {m}" for m in missed)
            lines.append("")

        unnamed = j.get("unnamed_patterns", [])
        if unnamed:
            lines.append("### Patterns I used but didn't name")
            lines.extend(
                f"- **{u.get('pattern_name', '')}** — {u.get('what_they_described', '')}"
                for u in unnamed
            )
            lines.append("")

        ref = sc.reference_solution or {}
        lines.append("### Reference summary")
        lines.append(ref.get("summary", "") + "\n")
        lines.append("---\n")

    content = "\n".join(lines)
    return PlainTextResponse(
        content,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=arch-trainer-sessions.md"},
    )
