"""Judge question prompts grounded in the generated startup blueprint."""

from collections.abc import Mapping
from dataclasses import dataclass
import textwrap


@dataclass(frozen=True)
class JudgeQuestion:
    question: str
    talking_points: tuple[tuple[str, str], ...]
    missing_sections: tuple[str, ...]


_QUESTION_SOURCES = (
    (
        "What proves this problem is real and urgent?",
        ("Problem Statement", "Target Customers", "Competitor Analysis"),
    ),
    (
        "Who is your first customer, and how will you reach them?",
        ("Target Customers", "Go-To-Market Strategy"),
    ),
    (
        "How will this become a sustainable business?",
        ("Revenue Model", "Business Model Canvas", "Estimated Budget"),
    ),
    (
        "Why will customers choose you over existing options?",
        ("Value Proposition", "Competitor Analysis", "SWOT Analysis"),
    ),
    (
        "What could derail the plan, and what will you prove next?",
        ("Risks & Mitigation", "12-Month Roadmap", "Immediate Next Steps"),
    ),
)


def build_judge_prep(sections: Mapping[str, str]) -> list[JudgeQuestion]:
    """Pair likely judge questions with concise excerpts from report sections."""
    questions = []
    for question, source_names in _QUESTION_SOURCES:
        talking_points = []
        missing_sections = []
        for source_name in source_names:
            content = sections.get(source_name, "")
            if isinstance(content, str) and content.strip():
                excerpt = textwrap.shorten(
                    " ".join(content.split()), width=420, placeholder="..."
                )
                talking_points.append((source_name, excerpt))
            else:
                missing_sections.append(source_name)
        questions.append(
            JudgeQuestion(
                question=question,
                talking_points=tuple(talking_points),
                missing_sections=tuple(missing_sections),
            )
        )
    return questions


def render_judge_prep(report) -> None:
    """Render report-backed talking points for common startup judge questions."""
    import streamlit as st

    sections = getattr(report, "sections", {})
    prep_items = build_judge_prep(sections if isinstance(sections, Mapping) else {})

    st.divider()
    st.subheader("Judge Prep")
    st.caption(
        "Likely questions with talking points taken from your blueprint. "
        "Verify each claim and fill evidence gaps before presenting."
    )

    if not any(item.talking_points for item in prep_items):
        st.info("Generate a blueprint with report sections to prepare judge answers.")
        return

    for item in prep_items:
        with st.expander(item.question):
            for source_name, excerpt in item.talking_points:
                st.markdown(f"**{source_name}**")
                st.write(excerpt)
            if item.missing_sections:
                st.caption(
                    "Prepare additional evidence for: "
                    + ", ".join(item.missing_sections)
                )