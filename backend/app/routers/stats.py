from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from ..auth import current_user
from ..db import get_db
from ..models import PatternGap, Session, User
from ..schemas import PatternGapStat

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/pattern-gaps", response_model=list[PatternGapStat])
def pattern_gaps(
    db: DbSession = Depends(get_db), user: User = Depends(current_user)
) -> list[PatternGapStat]:
    # Your gaps only — join through sessions to the owning user.
    stmt = (
        select(PatternGap.pattern_name, func.count().label("count"))
        .join(Session, PatternGap.session_id == Session.id)
        .where(Session.user_id == user.id)
        .group_by(PatternGap.pattern_name)
        .order_by(func.count().desc())
    )
    return [PatternGapStat(pattern_name=name, count=count) for name, count in db.execute(stmt)]


@router.get("/summary")
def summary(db: DbSession = Depends(get_db), user: User = Depends(current_user)) -> dict:
    base = select(Session).where(Session.user_id == user.id).subquery()
    total = db.scalar(select(func.count()).select_from(base)) or 0
    avg = db.scalar(select(func.avg(base.c.score)))
    return {
        "total_sessions": total,
        "average_score": round(float(avg), 2) if avg is not None else None,
    }
