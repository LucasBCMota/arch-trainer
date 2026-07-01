import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from ..auth import current_user, require_owner
from ..db import get_db
from ..models import InterviewRun, JobStatus, PatternGap, Session, User
from ..schemas import (
    InterviewCreate,
    InterviewOut,
    InterviewQuestionResult,
    InterviewSummary,
    PatternGapStat,
)

router = APIRouter(prefix="/api/interview", tags=["interview"])


@router.post("", response_model=InterviewOut)
def create_run(
    payload: InterviewCreate,
    db: DbSession = Depends(get_db),
    owner: User = Depends(require_owner),  # runs spend the server's keys
) -> InterviewRun:
    run = InterviewRun(
        user_id=owner.id,
        config={
            "count": payload.count,
            "difficulty": payload.difficulty.value,
            "types": [t.value for t in payload.exercise_types],
            "seconds": payload.seconds,
        },
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/{run_id}/summary", response_model=InterviewSummary)
def summary(
    run_id: uuid.UUID, db: DbSession = Depends(get_db), user: User = Depends(current_user)
) -> InterviewSummary:
    run = db.get(InterviewRun, run_id)
    if run is None or run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Interview run not found")

    sessions = list(
        db.scalars(
            select(Session)
            .where(Session.run_id == run_id, Session.status == JobStatus.ready)
            .order_by(Session.created_at.asc())
        ).all()
    )
    per_q = [
        InterviewQuestionResult(
            title=s.scenario.title, score=s.score, one_line_verdict=(s.judgment or {}).get("one_line_verdict", "")
        )
        for s in sessions
    ]
    avg = round(sum(s.score for s in sessions) / len(sessions), 2) if sessions else None

    gaps = db.execute(
        select(PatternGap.pattern_name, func.count().label("c"))
        .join(Session, PatternGap.session_id == Session.id)
        .where(Session.run_id == run_id)
        .group_by(PatternGap.pattern_name)
        .order_by(func.count().desc())
    )
    missed = [PatternGapStat(pattern_name=n, count=c) for n, c in gaps]

    return InterviewSummary(
        run_id=run_id,
        answered=len(sessions),
        average_score=avg,
        per_question=per_q,
        missed_patterns=missed,
    )
