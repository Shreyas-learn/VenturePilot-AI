"""
frontend/score_view.py — Startup Readiness Score visual rendering.

Renders the score gauge, dimension breakdown bars, and verdict
using only Streamlit + HTML/CSS (no external chart libraries).
"""

from __future__ import annotations

import streamlit as st

from config.constants import SCORE_DIMENSIONS
from core.report_builder import Report


def render_score_tab(report: Report) -> None:
    """Render the full Startup Readiness Score tab content.

    Displays the numeric gauge, dimension bars, the AI verdict text,
    and score band interpretation.

    Args:
        report: Generated report containing readiness_score and score_breakdown.
    """
    score = report.readiness_score
    breakdown = report.score_breakdown
    verdict_text = report.get_section("Startup Readiness Score")

    if score is None:
        st.info(
            "Startup Readiness Score is not available for this report.",
            icon="ℹ️",
        )
        return

    # ── Score gauge ──────────────────────────────────────────────────────────
    band_color, band_label = _score_band(score)

    st.markdown(
        f"""
        <div style="
            text-align: center;
            padding: 2rem 1rem 1.5rem 1rem;
            background: #f7f8fa;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            margin-bottom: 1.5rem;
        ">
            <div style="
                font-size: 5rem;
                font-weight: 900;
                color: {band_color};
                line-height: 1;
                margin-bottom: 0.25rem;
            ">{score}</div>
            <div style="
                font-size: 1rem;
                color: #57606a;
                margin-bottom: 0.5rem;
            ">out of 100</div>
            <div style="
                display: inline-block;
                background: {band_color};
                color: #fff;
                font-size: 0.85rem;
                font-weight: 600;
                padding: 0.25rem 0.9rem;
                border-radius: 999px;
            ">{band_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Score progress bar ────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="
            background: #e5e7eb;
            border-radius: 999px;
            height: 14px;
            margin-bottom: 2rem;
            overflow: hidden;
        ">
            <div style="
                background: {band_color};
                width: {score}%;
                height: 100%;
                border-radius: 999px;
                transition: width 0.5s ease;
            "></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Dimension breakdown ───────────────────────────────────────────────────
    if breakdown:
        st.markdown("#### Dimension Breakdown")
        for dimension, max_score in SCORE_DIMENSIONS.items():
            achieved = breakdown.get(dimension, 0)
            pct = int((achieved / max_score) * 100) if max_score else 0
            bar_color = _bar_color(pct)

            st.markdown(
                f"""
                <div style="margin-bottom: 0.75rem;">
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        font-size: 0.9rem;
                        margin-bottom: 0.2rem;
                        color: #1f2328;
                    ">
                        <span><strong>{dimension}</strong></span>
                        <span style="color: #57606a;">{achieved} / {max_score}</span>
                    </div>
                    <div style="
                        background: #e5e7eb;
                        border-radius: 999px;
                        height: 10px;
                        overflow: hidden;
                    ">
                        <div style="
                            background: {bar_color};
                            width: {pct}%;
                            height: 100%;
                            border-radius: 999px;
                        "></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Score band legend ────────────────────────────────────────────────────
    st.markdown("#### Score Bands")
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown("🟢 **85–100**  \nInvestor-ready")
    col2.markdown("🟡 **70–84**  \nStrong — address gaps")
    col3.markdown("🟠 **55–69**  \nPromising — work needed")
    col4.markdown("🔴 **< 55**  \nNeeds rethinking")

    # ── AI Verdict ───────────────────────────────────────────────────────────
    if verdict_text:
        st.markdown("---")
        st.markdown("#### AI Verdict")
        st.markdown(verdict_text)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _score_band(score: int) -> tuple[str, str]:
    """Return (hex_color, label) for a given score.

    Args:
        score: Integer score 0–100.

    Returns:
        Tuple of (CSS hex color string, band label string).
    """
    if score >= 85:
        return "#22863a", "🟢 Investor-Ready"
    if score >= 70:
        return "#b08800", "🟡 Strong Foundation"
    if score >= 55:
        return "#e36209", "🟠 Promising"
    return "#cb2431", "🔴 Needs Rethinking"


def _bar_color(pct: int) -> str:
    """Return a CSS color for a dimension progress bar based on percentage.

    Args:
        pct: Percentage achieved (0–100).

    Returns:
        CSS hex color string.
    """
    if pct >= 80:
        return "#22863a"
    if pct >= 60:
        return "#3b82d4"
    if pct >= 40:
        return "#e36209"
    return "#cb2431"
