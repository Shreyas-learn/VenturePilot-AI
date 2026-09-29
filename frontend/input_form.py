"""
frontend/input_form.py — Startup idea input form.

Renders the main data-collection form and returns a validated
StartupInput dataclass when the user submits, or None otherwise.
"""

from typing import Optional

import streamlit as st

from config.constants import INDUSTRIES, COUNTRIES, STARTUP_STAGES, BUDGET_OPTIONS
from core.startup_input import StartupInput


def render_input_form() -> Optional[StartupInput]:
    """Render the startup input form and return validated input on submission.

    Returns:
        A :class:`StartupInput` instance when the form is submitted with valid
        data, or ``None`` when the form has not been submitted yet.
    """
    with st.form(key="startup_form", clear_on_submit=False):
        st.markdown("### 📋 Tell us about your startup")

        col1, col2 = st.columns(2)

        with col1:
            startup_name = st.text_input(
                "Startup Name *",
                placeholder="e.g. GreenHarvest",
                help="The name of your startup or venture.",
            )
            industry = st.selectbox(
                "Industry *",
                options=INDUSTRIES,
                help="Select the industry your startup operates in.",
            )
            budget = st.selectbox(
                "Estimated Budget *",
                options=BUDGET_OPTIONS,
                help="Select your approximate initial budget range.",
            )

        with col2:
            country = st.selectbox(
                "Country *",
                options=COUNTRIES,
                help="Primary country of operation.",
            )
            startup_stage = st.selectbox(
                "Startup Stage *",
                options=STARTUP_STAGES,
                help="Current stage of your startup.",
            )

        startup_idea = st.text_area(
            "Startup Idea *",
            placeholder=(
                "Describe your startup idea in detail. "
                "What problem does it solve? Who are your customers? "
                "What makes it unique?"
            ),
            height=150,
            help="The more detail you provide, the better your blueprint will be.",
        )

        submitted = st.form_submit_button(
            "🚀 Generate Blueprint",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        errors = _validate(startup_name, startup_idea)
        if errors:
            for error in errors:
                st.error(error)
            return None

        return StartupInput(
            startup_name=startup_name.strip(),
            startup_idea=startup_idea.strip(),
            industry=industry,
            country=country,
            budget=budget,
            startup_stage=startup_stage,
        )

    return None


def _validate(startup_name: str, startup_idea: str) -> list[str]:
    """Return a list of validation error messages, or an empty list if valid.

    Args:
        startup_name: Raw startup name value from the form.
        startup_idea: Raw startup idea value from the form.

    Returns:
        List of human-readable error strings.
    """
    errors: list[str] = []

    if not startup_name or not startup_name.strip():
        errors.append("⚠️ Please enter your startup name.")

    if not startup_idea or len(startup_idea.strip()) < 20:
        errors.append(
            "⚠️ Please describe your startup idea in at least 20 characters."
        )

    return errors
