"""Scenario-generation and judging prompts.

These are the core of the tool's value — see CLAUDE.md "AI Prompt Changes".
The judging user prompt keeps the candidate's answer LAST; moving it changes
scoring behavior, so don't reorder it.
"""

SCENARIO_SYSTEM = (
    "You are a principal engineer designing a system-design exercise. You produce two things: a "
    "realistic scenario, and a hidden reference solution. Be concrete and specific — invent a "
    "real-sounding product/system, not abstract placeholders. Output ONLY valid JSON, no markdown "
    "fences, no preamble."
)

DIFFICULTY_CALIBRATION = {
    "feature": (
        "feature-level: a bounded change to one service. Tests whether obvious constraints are "
        "caught."
    ),
    "platform": (
        "platform-level: touches other teams/services, external contracts, data ownership across "
        "boundaries."
    ),
    "principal": (
        "principal-level: org-wide implications, migration/rollout strategy, irreversible "
        "decisions, multi-year tradeoffs."
    ),
}

SCENARIO_JSON_SHAPE = """{
  "title": "short scenario title",
  "context": "2-4 sentences of system/business context",
  "problem": "the specific problem or feature request, written like a real ticket or PM ask",
  "constraints": ["list", "of", "given constraints or non-functional requirements"],
  "reference_solution": {
    "summary": "2-3 sentence summary of the recommended approach",
    "key_decisions": [
      {"decision": "...", "pattern_name": "formal pattern name or null", "rationale": "why this over alternatives"}
    ],
    "tradeoffs_considered": ["alternative approach and why it was rejected"],
    "failure_modes_addressed": ["specific failure mode and how the design handles it"],
    "open_questions_for_pm": ["questions a senior engineer would still ask"]
  }
}"""


STRUCTURED_ADDENDUM = """
This is a STRUCTURED DESIGN exercise. The candidate will fill in a templated answer and you grade the
content of their design. Add these fields to the JSON above:
- "response_template": an array of {"section": "...", "guidance": "..."} objects — the sections the
  candidate should fill in, TAILORED to this scenario (e.g. "Requirements", "Infrastructure",
  "Actions per requirement", "Data model"). ALWAYS include a final section {"section": "Diagram",
  "guidance": "Provide a Mermaid diagram of your architecture."}.
- "context_diagram": a Mermaid diagram (string) of the CURRENT/given system if one helps, else null.
- inside "reference_solution", also add "diagram_mermaid": a Mermaid diagram of the RECOMMENDED
  architecture.
All Mermaid must be valid `flowchart TD` / `graph TD` syntax."""


def scenario_user_prompt(difficulty: str, focus_area: str, structured: bool = False) -> str:
    calibration = DIFFICULTY_CALIBRATION[difficulty]
    focus_line = (
        "Any focus area is fine."
        if focus_area in ("", "any")
        else f"Bias the scenario toward this focus area: {focus_area}."
    )
    addendum = STRUCTURED_ADDENDUM if structured else ""
    return (
        f"Generate a system-design exercise at this difficulty:\n{calibration}\n\n"
        f"{focus_line}\n\n"
        f"Respond with JSON in exactly this shape:\n{SCENARIO_JSON_SHAPE}{addendum}"
    )


# ---- Language-gotcha & algorithms exercises (QA-shaped scenario) ----
QA_JSON_SHAPE = """{
  "title": "short title",
  "context": "setup for the question; put any code in a fenced ```code block",
  "problem": "the exact question or task the candidate must answer",
  "constraints": ["what a complete answer should address"],
  "reference_solution": {
    "summary": "the correct answer / explanation",
    "key_points": ["the points a correct answer must hit"],
    "common_mistakes": ["frequent wrong answers / misconceptions"]
  }
}"""

LANGUAGE_SYSTEM = (
    "You are a senior engineer writing a single sharp question about a programming language's "
    "specific behavior — a subtle gotcha, edge case, or 'what happens when…'. Be concrete: include a "
    "short, runnable code snippet when it sharpens the question. Output ONLY valid JSON, no markdown "
    "fences, no preamble."
)


def language_user_prompt(language: str) -> str:
    return (
        f"Write one {language} language-behavior question — a subtle gotcha or edge case a strong "
        f"{language} dev could still get wrong (e.g. mutable default arguments, closure capture, "
        "integer/reference semantics, evaluation order). The candidate will explain what happens and "
        f"why.\n\nRespond with JSON in exactly this shape:\n{QA_JSON_SHAPE}"
    )


ALGORITHMS_SYSTEM = (
    "You are a senior engineer writing one algorithms/data-structures exercise for practice. Output "
    "ONLY valid JSON, no markdown fences, no preamble."
)


def algorithms_user_prompt(language: str) -> str:
    lang_line = (
        "If it is an implementation task, the candidate may use any language."
        if language in ("", "any", None)
        else f"If it is an implementation task, target {language}."
    )
    runnable = (language or "").lower() in ("python", "javascript")
    tests_addendum = ""
    if runnable:
        tests_addendum = (
            "\n\nIf (and only if) this is an IMPLEMENTATION task, ALSO add two top-level string "
            'fields:\n- "code_entry": a minimal starter stub the candidate fills in (the required '
            f"signature/skeleton in {language}, with a TODO body).\n"
            '- "code_tests": a SELF-CONTAINED test harness in ' + language + " that will be appended "
            "AFTER the candidate's code and run together. It must call the candidate's implementation "
            "on several cases, print `PASS`/`FAIL: <detail>` per case, and finish with EXACTLY one "
            "line: `__TESTS__ <passed> <total>`. Do not redefine the candidate's functions."
        )
    return (
        "Write ONE algorithms/data-structures exercise. Randomly pick ONE of two kinds and say which "
        "in the problem: (a) a CONCEPT/COMPLEXITY question (e.g. 'what is the Big-O of insert and "
        "remove in a binary heap, and why'), or (b) an IMPLEMENTATION task (e.g. 'implement a "
        f"min-heap with push/pop'). {lang_line} The reference_solution.summary must give the correct "
        "answer (including Big-O where relevant) and, for implementation tasks, a correct reference "
        f"implementation in a fenced code block.{tests_addendum}\n\n"
        f"Respond with JSON in exactly this shape:\n{QA_JSON_SHAPE}"
    )


JUDGE_SYSTEM = (
    "You are a principal engineer judging a candidate's architectural reasoning against a "
    "known-correct reference solution. Be honest and specific — this is for skill-building, not "
    "encouragement. Identify exactly which named patterns the candidate's answer demonstrates but "
    "failed to name, where their reasoning matched the reference, and where it genuinely diverged "
    "or fell short. Do not be harsh for its own sake, but do not soften real gaps. Output ONLY "
    "valid JSON, no markdown fences."
)

JUDGE_JSON_SHAPE = """{
  "overall_assessment": "feature-level | platform-level | principal-level",
  "matched_points": ["..."],
  "missed_points": ["..."],
  "unnamed_patterns": [{"what_they_described": "...", "pattern_name": "..."}],
  "genuine_disagreements": ["cases where candidate's approach is defensible, not wrong"],
  "communication_gaps": ["reasoning was present but not clearly justified"],
  "score_1_to_5": 0,
  "one_line_verdict": "single direct sentence"
}"""


# ---- Study / cheat-sheet generation (Markdown output, NOT JSON) ----
# Prose Markdown is far more robust on small/free models than the strict nested
# JSON the scenario generator needs — so these never go through parse_model_json.

STUDY_SYSTEM = (
    "You are a principal engineer writing a focused study note on a named software-architecture "
    "pattern or concept, for an engineer practicing system design. Be concrete and specific; prefer "
    "real examples over abstractions. Output GitHub-flavored Markdown only — no preamble, no code "
    "fences around the whole document."
)


def study_user_prompt(topic: str) -> str:
    return (
        f"Write a study note on: {topic}\n\n"
        "Use these Markdown sections (## headings):\n"
        "## What it is\n"
        "## When to use it (and when not to)\n"
        "## Canonical shape\n"
        "## Key trade-offs\n"
        "## Failure modes it addresses\n"
        "## Commonly confused with\n"
        "## Worked mini-example\n"
    )


CHEATSHEET_SYSTEM = (
    "You are a principal engineer writing a terse one-page quick-reference card for a software-"
    "architecture pattern. Dense and scannable, no fluff. Output GitHub-flavored Markdown only."
)


def cheatsheet_user_prompt(topic: str) -> str:
    return (
        f"Write a one-page cheat-sheet for: {topic}\n\n"
        "Keep it tight. Use these Markdown sections (## headings):\n"
        "## Definition (one sentence)\n"
        "## Use when\n"
        "## Shape (3-5 bullets)\n"
        "## Pitfalls\n"
        "## Related patterns\n"
    )


JUDGE_STRUCTURED_JSON_SHAPE = """{
  "overall_assessment": "feature-level | platform-level | principal-level",
  "matched_points": ["..."],
  "missed_points": ["..."],
  "unnamed_patterns": [{"what_they_described": "...", "pattern_name": "..."}],
  "requirement_coverage": [
    {"requirement": "the constraint/requirement", "status": "covered | partial | missing", "comment": "how the design addresses it, or what's missing"}
  ],
  "genuine_disagreements": ["cases where candidate's approach is defensible, not wrong"],
  "communication_gaps": ["reasoning was present but not clearly justified"],
  "score_1_to_5": 0,
  "one_line_verdict": "single direct sentence"
}"""


# ---- Hints & follow-ups (Markdown output, not JSON) ----
HINT_SYSTEM = (
    "You are a coach giving a candidate ONE short nudge on a practice exercise. Point them toward the "
    "key consideration they should think about — do NOT give the answer, name the exact pattern, or "
    "solve it. One or two sentences. Output plain Markdown."
)


def hint_user_prompt(scenario_block: str) -> str:
    return f"Exercise:\n{scenario_block}\n\nGive one short hint (no spoilers)."


FOLLOWUP_SYSTEM = (
    "You are a principal engineer answering a candidate's follow-up question about a practice "
    "exercise and its reference solution. Be direct and concrete. Output Markdown; use fenced code "
    "blocks for code and ```mermaid for diagrams."
)


def followup_user_prompt(scenario_block: str, reference_block: str, question: str) -> str:
    return (
        f"## EXERCISE\n{scenario_block}\n\n"
        f"## REFERENCE SOLUTION\n{reference_block}\n\n"
        f"## QUESTION\n{question}\n\nAnswer it."
    )


JUDGE_INTROS = {
    "language": (
        "Judge whether the candidate correctly explains the language behavior. Mark what they got "
        "right and what is wrong or missing versus the reference; correct any misconception plainly."
    ),
    "algorithms": (
        "Judge correctness: for a complexity question, is the Big-O right and the reasoning sound; "
        "for an implementation, is the code correct (note bugs/edge cases) and what is its actual "
        "time/space complexity. Compare against the reference."
    ),
}


def judge_user_prompt(
    scenario_block: str,
    reference_block: str,
    candidate_answer: str,
    *,
    structured: bool = False,
    requirements: list[str] | None = None,
    exercise_type: str = "free_form",
) -> str:
    if exercise_type in JUDGE_INTROS:
        return (
            f"{JUDGE_INTROS[exercise_type]}\n\n"
            f"## QUESTION / TASK\n{scenario_block}\n\n"
            f"## REFERENCE ANSWER (ground truth)\n{reference_block}\n\n"
            f"## CANDIDATE'S ANSWER\n{candidate_answer}\n\n"
            f"Respond with JSON in exactly this shape (leave unnamed_patterns empty):\n{JUDGE_JSON_SHAPE}"
        )
    if structured:
        reqs = "\n".join(f"- {r}" for r in (requirements or [])) or "(none listed)"
        return (
            "Judge the candidate's DESIGN by its actual content, not just whether they named "
            "patterns. For EACH requirement below, decide if the design covers it (covered / partial "
            "/ missing) and why. The candidate's answer includes a Mermaid diagram — read it as part "
            "of the design.\n\n"
            f"## SCENARIO\n{scenario_block}\n\n"
            f"## REQUIREMENTS TO COVER\n{reqs}\n\n"
            f"## REFERENCE SOLUTION (ground truth, incl. its Mermaid diagram)\n{reference_block}\n\n"
            f"## CANDIDATE'S ANSWER\n{candidate_answer}\n\n"
            f"Respond with JSON in exactly this shape:\n{JUDGE_STRUCTURED_JSON_SHAPE}"
        )
    return (
        "Judge the candidate's architectural reasoning.\n\n"
        f"## SCENARIO\n{scenario_block}\n\n"
        f"## REFERENCE SOLUTION (ground truth)\n{reference_block}\n\n"
        f"## CANDIDATE'S ANSWER\n{candidate_answer}\n\n"
        f"Respond with JSON in exactly this shape:\n{JUDGE_JSON_SHAPE}"
    )
