import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .models import Difficulty, Visibility


# ---- Reference solution shape (generated, ground truth) ----
class KeyDecision(BaseModel):
    decision: str
    pattern_name: str | None = None
    rationale: str


class ReferenceSolution(BaseModel):
    summary: str
    key_decisions: list[KeyDecision] = []
    tradeoffs_considered: list[str] = []
    failure_modes_addressed: list[str] = []
    open_questions_for_pm: list[str] = []


# ---- Judgment shape ----
class UnnamedPattern(BaseModel):
    what_they_described: str
    pattern_name: str


class Judgment(BaseModel):
    overall_assessment: str
    matched_points: list[str] = []
    missed_points: list[str] = []
    unnamed_patterns: list[UnnamedPattern] = []
    genuine_disagreements: list[str] = []
    communication_gaps: list[str] = []
    score_1_to_5: int
    one_line_verdict: str


# ---- Scenarios ----
class ScenarioCreate(BaseModel):
    difficulty: Difficulty
    focus_area: str = "any"
    model: str | None = None  # optional per-request override of LLM_MODEL


class ScenarioOut(BaseModel):
    """Safe shape — deliberately has NO reference_solution field so it can never
    leak the hidden reference, even via from_attributes auto-population."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    difficulty: Difficulty
    focus_area: str
    title: str
    context: str
    problem: str
    constraints: list
    model: str
    visibility: Visibility = Visibility.private


class ScenarioRevealOut(ScenarioOut):
    """Used only on the result screen via ?reveal=true."""

    reference_solution: ReferenceSolution


# ---- Sessions ----
class SessionCreate(BaseModel):
    scenario_id: uuid.UUID
    user_answer: str


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scenario_id: uuid.UUID
    created_at: datetime
    user_answer: str
    judgment: Judgment
    score: int
    model: str
    visibility: Visibility = Visibility.private
    author: str | None = None


class SessionResult(SessionOut):
    """Returned right after judging — includes the full reference for the result screen."""

    reference_solution: ReferenceSolution


# ---- Stats / models ----
class PatternGapStat(BaseModel):
    pattern_name: str
    count: int


class ModelsInfo(BaseModel):
    current: str
    available: list[str]
    suggested: dict[str, list[str]]


# ---- Study notes / artifacts ----
from .models import StudyNoteKind  # noqa: E402


class StudyNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    kind: StudyNoteKind
    topic: str
    content_md: str
    model: str
    pinned: bool
    visibility: Visibility = Visibility.private
    author: str | None = None


class StudyCreate(BaseModel):
    topic: str
    model: str | None = None  # override LLM_MODEL for this generation


class StudyImport(BaseModel):
    topic: str
    kind: StudyNoteKind
    content_md: str
    source: str | None = None  # origin label, e.g. "claude.ai opus"; stored in `model`


class StudyEdit(BaseModel):
    topic: str | None = None
    content_md: str | None = None


class PinBody(BaseModel):
    pinned: bool


class VisibilityBody(BaseModel):
    visibility: Visibility


class FavoriteModelsBody(BaseModel):
    models: list[str]


class ReferenceArtifactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    difficulty: Difficulty
    focus_area: str
    title: str
    problem: str
    model: str
    pinned: bool
    visibility: Visibility = Visibility.private
    author: str | None = None
    reference_solution: ReferenceSolution
