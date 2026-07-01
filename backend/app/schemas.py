import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .models import Difficulty, ExerciseType, JobStatus, Visibility


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
    # structured exercises: a Mermaid diagram of the recommended architecture
    diagram_mermaid: str | None = None
    # language/algorithms exercises: prominent correct-answer detail
    key_points: list[str] = []
    common_mistakes: list[str] = []


# ---- Judgment shape ----
class UnnamedPattern(BaseModel):
    what_they_described: str
    pattern_name: str


class RequirementCoverage(BaseModel):
    requirement: str
    status: str  # covered | partial | missing
    comment: str = ""


class Judgment(BaseModel):
    overall_assessment: str
    matched_points: list[str] = []
    missed_points: list[str] = []
    unnamed_patterns: list[UnnamedPattern] = []
    genuine_disagreements: list[str] = []
    communication_gaps: list[str] = []
    requirement_coverage: list[RequirementCoverage] = []  # structured exercises
    score_1_to_5: int
    one_line_verdict: str


# ---- Scenarios ----
class ScenarioCreate(BaseModel):
    difficulty: Difficulty
    focus_area: str = "any"
    exercise_type: ExerciseType = ExerciseType.free_form
    language: str | None = None  # for language/algorithms exercises
    model: str | None = None  # optional per-request override of LLM_MODEL
    variation_of: uuid.UUID | None = None  # make a harder variation of this scenario
    focus_pattern: str | None = None  # bias the exercise toward this pattern (smart review)


class FollowupBody(BaseModel):
    question: str


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
    exercise_type: ExerciseType = ExerciseType.free_form
    response_template: list = []  # visible answer-section template (structured only)
    context_diagram: str | None = None
    language: str | None = None
    visibility: Visibility = Visibility.private
    status: JobStatus = JobStatus.ready
    error: str | None = None


class ScenarioRevealOut(ScenarioOut):
    """Used only on the result screen via ?reveal=true."""

    reference_solution: ReferenceSolution


class ScenarioListItem(ScenarioOut):
    """Your own scenarios, with whether you've answered one — powers resume / re-attempt."""

    answered: bool = False


# ---- Sessions ----
class SessionCreate(BaseModel):
    scenario_id: uuid.UUID
    user_answer: str
    answer_freehand: dict | None = None  # Excalidraw scene; stored, never judged


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scenario_id: uuid.UUID
    created_at: datetime
    user_answer: str
    judgment: dict = {}  # empty until judged; full judgment shape once ready
    score: int
    model: str
    visibility: Visibility = Visibility.private
    author: str | None = None
    status: JobStatus = JobStatus.ready
    error: str | None = None


class SessionDetail(SessionOut):
    """GET /api/sessions/{id} — includes the reference once judging is ready."""

    reference_solution: ReferenceSolution | None = None
    answer_freehand: dict | None = None  # for side-by-side comparison on results


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
    status: JobStatus = JobStatus.ready
    error: str | None = None


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
