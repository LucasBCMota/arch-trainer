import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Difficulty(str, enum.Enum):
    feature = "feature"
    platform = "platform"
    principal = "principal"


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty, name="difficulty"))
    focus_area: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(Text)
    context: Mapped[str] = mapped_column(Text)
    problem: Mapped[str] = mapped_column(Text)
    constraints: Mapped[list] = mapped_column(JSONB, default=list)
    reference_solution: Mapped[dict] = mapped_column(JSONB, default=dict)
    model: Mapped[str] = mapped_column(String(128))

    sessions: Mapped[list["Session"]] = relationship(back_populates="scenario")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scenarios.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user_answer: Mapped[str] = mapped_column(Text)
    judgment: Mapped[dict] = mapped_column(JSONB, default=dict)
    score: Mapped[int] = mapped_column(Integer)
    model: Mapped[str] = mapped_column(String(128))

    scenario: Mapped["Scenario"] = relationship(back_populates="sessions")
    pattern_gaps: Mapped[list["PatternGap"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class PatternGap(Base):
    __tablename__ = "pattern_gaps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"))
    pattern_name: Mapped[str] = mapped_column(Text)
    what_they_described: Mapped[str] = mapped_column(Text)

    session: Mapped["Session"] = relationship(back_populates="pattern_gaps")
