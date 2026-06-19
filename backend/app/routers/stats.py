from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from ..db import get_db
from ..models import PatternGap, Session
from ..schemas import PatternGapStat

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/pattern-gaps", response_model=list[PatternGapStat])
def pattern_gaps(db: DbSession = Depends(get_db)) -> list[PatternGapStat]:
    stmt = (
        select(PatternGap.pattern_name, func.count().label("count"))
        .group_by(PatternGap.pattern_name)
        .order_by(func.count().desc())
    )
    return [PatternGapStat(pattern_name=name, count=count) for name, count in db.execute(stmt)]


@router.get("/summary")
def summary(db: DbSession = Depends(get_db)) -> dict:
    total = db.scalar(select(func.count()).select_from(Session)) or 0
    avg = db.scalar(select(func.avg(Session.score)))
    return {
        "total_sessions": total,
        "average_score": round(float(avg), 2) if avg is not None else None,
    }
