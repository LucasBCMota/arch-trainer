import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
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


class StudyNoteKind(str, enum.Enum):
    deep_dive = "deep_dive"
    cheat_sheet = "cheat_sheet"


class ExerciseType(str, enum.Enum):
    free_form = "free_form"    # free-text answer, pattern-naming focus
    structured = "structured"  # templated answer, per-requirement content grading
    language = "language"      # language-specific behavior/gotcha question
    algorithms = "algorithms"  # complexity/concept or implementation task


class Visibility(str, enum.Enum):
    private = "private"
    public = "public"


class JobStatus(str, enum.Enum):
    pending = "pending"   # queued, not yet picked up
    running = "running"   # a worker is processing it
    ready = "ready"       # finished successfully
    error = "error"       # failed (see .error)


def _status_col() -> Mapped["JobStatus"]:
    return mapped_column(
        Enum(JobStatus, name="jobstatus"),
        default=JobStatus.ready,
        server_default="ready",  # existing rows are already complete
        index=True,
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)  # Auth0 subject
    email: Mapped[str] = mapped_column(String(320), index=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    picture: Mapped[str | None] = mapped_column(Text, nullable=True)
    # User's saved "provider:model" strings for quick switching.
    favorite_models: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")

    @property
    def display_name(self) -> str:
        return self.name or (self.email.split("@")[0] if self.email else "user")


# Reusable column factories for the owner_id / visibility pair added to ownable rows.
def _owner_id_col() -> Mapped[uuid.UUID | None]:
    return mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)


def _visibility_col() -> Mapped[Visibility]:
    return mapped_column(
        Enum(Visibility, name="visibility"),
        default=Visibility.private,
        server_default="private",
    )


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
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    exercise_type: Mapped[ExerciseType] = mapped_column(
        Enum(ExerciseType, name="exercisetype"),
        default=ExerciseType.free_form,
        server_default="free_form",
    )
    # Visible answer-section template for structured exercises (no reference leak).
    response_template: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    # Optional Mermaid diagram shown with the problem context.
    context_diagram: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Selected language for language/algorithms exercises ("any" allowed for algorithms).
    language: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # Extra generation instruction (e.g. "harder variation of …" / "target pattern …").
    gen_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[uuid.UUID | None] = _owner_id_col()
    visibility: Mapped[Visibility] = _visibility_col()
    status: Mapped[JobStatus] = _status_col()
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # When the worker marked it 'running' — reclaim keys off this, not created_at.
    running_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User | None"] = relationship()
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
    # Optional Excalidraw freehand scene — stored for self-comparison, never judged.
    answer_freehand: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    user_id: Mapped[uuid.UUID | None] = _owner_id_col()
    visibility: Mapped[Visibility] = _visibility_col()
    status: Mapped[JobStatus] = _status_col()
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # When the worker marked it 'running' — reclaim keys off this, not created_at.
    running_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User | None"] = relationship()
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


class StudyNote(Base):
    __tablename__ = "study_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    kind: Mapped[StudyNoteKind] = mapped_column(Enum(StudyNoteKind, name="studynotekind"))
    topic: Mapped[str] = mapped_column(Text)
    content_md: Mapped[str] = mapped_column(Text)
    # Origin: an LLM model id (e.g. "openrouter:...") or a manual source label.
    model: Mapped[str] = mapped_column(String(128))
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    user_id: Mapped[uuid.UUID | None] = _owner_id_col()
    visibility: Mapped[Visibility] = _visibility_col()
    status: Mapped[JobStatus] = _status_col()
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # When the worker marked it 'running' — reclaim keys off this, not created_at.
    running_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User | None"] = relationship()
