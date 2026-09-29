"""
frontend/report_view.py — Report display and section rendering.

Renders a generated Report using Streamlit tabs and expandable sections.
Provides live PDF and Markdown download buttons via utils/export.
"""

import streamlit as st

from core.report_builder import Report
from config.constants import REPORT_SECTIONS
from frontend.score_view import render_score_tab
from utils.export import export_markdown, export_pdf


# ---------------------------------------------------------------------------
# Tab → section mapping
# ---------------------------------------------------------------------------

_TAB_SECTIONS: dict[str, list[str]] = {
    "📄 Business Blueprint": [
        "Executive Summary",
        "Problem Statement",
        "Proposed Solution",
        "Vision & Mission",
        "Target Customers",
        "Value Proposition",
        "Business Model Canvas",
        "Revenue Model",
    ],
    "💰 Funding Advisor": [
        "Estimated Budget",
        "Funding Opportunities",
        "Government Schemes",
        "Incubator Recommendations",
    ],
    "📊 Market Intelligence": [
        "Competitor Analysis",
        "SWOT Analysis",
    ],
    "🗓️ Roadmap": [
        "Go-To-Market Strategy",
        "12-Month Roadmap",
        "Risks & Mitigation",
    ],
    "🎤 Investor Pitch": [
        "Investor Elevator Pitch",
        "Final Recommendation",
    ],
    "⭐ Startup Score": [],   # rendered by score_view
    "✅ Action Plan": [
        "Immediate Next Steps",
    ],
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def render_report(report: Report) -> None:
    """Render the full blueprint report inside organised tabs.

    Args:
        report: A fully populated :class:`Report` instance.
    """
    st.success(
        f"✅ Blueprint generated for **{report.startup_input.startup_name}**"
        + (
            f" &nbsp;|&nbsp; Readiness Score: **{report.readiness_score} / 100**"
            if report.readiness_score is not None
            else ""
        )
    )
    st.markdown("---")

    tab_labels = list(_TAB_SECTIONS.keys())
    tabs = st.tabs(tab_labels)

    for tab, label in zip(tabs, tab_labels):
        with tab:
            if label == "⭐ Startup Score":
                render_score_tab(report)
            else:
                _render_tab_sections(report, _TAB_SECTIONS[label])

    st.markdown("---")
    _render_export_buttons(report)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _render_tab_sections(report: Report, section_names: list[str]) -> None:
    """Render a list of sections as expandable blocks inside a tab.

    Args:
        report:        The generated report.
        section_names: Ordered list of section names to display.
    """
    for name in section_names:
        content = report.get_section(name)
        with st.expander(f"**{name}**", expanded=True):
            if content:
                st.markdown(content)
            else:
                st.caption("_This section was not returned by the model._")


def _render_export_buttons(report: Report) -> None:
    """Render PDF and Markdown download buttons.

    Both exports are generated on demand when the user clicks the button.

    Args:
        report: The generated report.
    """
    st.markdown("### 📥 Export Report")
    col1, col2 = st.columns(2)

    with col1:
        md_content = export_markdown(report)
        st.download_button(
            label="📄 Download Markdown",
            data=md_content,
            file_name=f"{report.startup_input.startup_name.replace(' ', '_')}_blueprint.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col2:
        try:
            pdf_bytes = export_pdf(report)
            st.download_button(
                label="📑 Download PDF",
                data=pdf_bytes,
                file_name=f"{report.startup_input.startup_name.replace(' ', '_')}_blueprint.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(
                f"⚠️ PDF generation failed: {exc}  \n"
                "Please download the Markdown version instead.",
                icon="⚠️",
            )
