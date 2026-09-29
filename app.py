"""
VenturePilot AI — Main Streamlit Entry Point

Responsibilities (and ONLY these):
    1. Configure the Streamlit page
    2. Validate Gemini configuration on startup
    3. Render the sidebar (with RAG status)
    4. Render the page header
    5. Collect startup input from the user
    6. Call the orchestrator to generate the blueprint
    7. Render the generated report

No business logic lives here.
"""

import streamlit as st

from config.settings import settings, ConfigurationError
from utils.logger import get_logger
from frontend.layout import configure_page, render_sidebar, render_header
from frontend.input_form import render_input_form
from frontend.report_view import render_report
from core.orchestrator import generate_blueprint
from gemini.gemini_client import GeminiAuthenticationError, GeminiGenerationError
from rag.rag_pipeline import init_rag, RAGStatus

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------

_SESSION_KEYS: dict[str, object] = {
    "report":        None,
    "startup_input": None,
    "rag_status":    None,
}


def _init_session_state() -> None:
    """Ensure all expected session-state keys exist before first render.

    Initialising upfront prevents KeyError on any rerun before the first
    successful generation.
    """
    for key, default in _SESSION_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = default


# ---------------------------------------------------------------------------
# RAG initialisation (cached across reruns)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="📚 Indexing knowledge base…")
def _load_rag() -> RAGStatus:
    """Initialise the RAG pipeline exactly once per server process.

    :func:`st.cache_resource` ensures this is not re-executed on every
    Streamlit rerun, avoiding redundant PDF scanning and indexing.

    Returns:
        A :class:`RAGStatus` snapshot describing the pipeline state.
    """
    logger.info("RAG pipeline initialisation requested.")
    status = init_rag()
    logger.info(
        "RAG ready — %d PDF(s), %d chunk(s), provider: %s.",
        status.pdf_files_found,
        status.total_chunks,
        status.embedding_provider,
    )
    return status


# ---------------------------------------------------------------------------
# Configuration banner
# ---------------------------------------------------------------------------

def _render_config_warning() -> bool:
    """Display a warning banner when Gemini credentials are incomplete.

    Returns:
        True when all required credentials are present, False otherwise.
    """
    missing = settings.missing_vars()
    if not missing:
        return True

    st.warning(
        "⚠️ **Gemini API key is not configured.**\n\n"
        f"Missing environment variables: `{'`, `'.join(missing)}`\n\n"
        "Copy `.env.example` to `.env` and fill in your `GEMINI_API_KEY`.\n\n"
        "See the **README** for detailed setup instructions.",
        icon="⚠️",
    )
    return False


# ---------------------------------------------------------------------------
# Blueprint generation
# ---------------------------------------------------------------------------

def _run_generation(startup_input) -> None:
    """Run blueprint generation and update session state.

    Handles all error cases and displays user-friendly messages.
    Separates generation logic from the main render flow.

    Args:
        startup_input: Validated :class:`~core.startup_input.StartupInput`.
    """
    logger.info(
        "Blueprint generation requested — startup='%s', industry='%s', stage='%s'.",
        startup_input.startup_name,
        startup_input.industry,
        startup_input.startup_stage,
    )

    info_box = st.info(
        "🧠 **Generating your startup blueprint with Google Gemini…**  \n"
        "This typically takes 60–120 seconds. Please wait.",
        icon="🧠",
    )

    try:
        with st.spinner("Calling Google Gemini API — 5 sections being generated…"):
            report = generate_blueprint(startup_input)

        info_box.empty()
        st.session_state.report = report
        st.session_state.startup_input = startup_input

        logger.info(
            "Blueprint generation succeeded for '%s' — score=%s.",
            startup_input.startup_name,
            report.readiness_score,
        )

    except GeminiAuthenticationError as exc:
        info_box.empty()
        logger.error("Gemini authentication error: %s", exc)
        st.error(
            "🔐 **Authentication failed.**\n\n"
            f"{exc}\n\n"
            "Please verify `GEMINI_API_KEY` in your `.env` file or Streamlit secrets.",
        )

    except GeminiGenerationError as exc:
        info_box.empty()
        logger.error("Gemini generation error: %s", exc)
        st.error(
            "🤖 **Google Gemini could not generate a response.**\n\n"
            f"{exc}\n\n"
            "This may be a transient issue. Please try again in a moment.",
        )

    except Exception as exc:
        info_box.empty()
        logger.exception("Unexpected error during blueprint generation.")
        st.error(
            "❌ **An unexpected error occurred.**\n\n"
            f"`{type(exc).__name__}: {exc}`\n\n"
            "Check `logs/app.log` for details.",
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Application entry point."""
    configure_page()
    _init_session_state()

    # RAG initialisation — runs once, cached for the process lifetime
    rag_status: RAGStatus = _load_rag()
    st.session_state.rag_status = rag_status

    render_sidebar(rag_status)
    render_header()

    st.divider()

    is_configured = _render_config_warning()

    startup_input = render_input_form()

    if startup_input and is_configured:
        # Only re-generate when the user submits a different input
        if startup_input != st.session_state.startup_input:
            _run_generation(startup_input)

    elif startup_input and not is_configured:
        st.error(
            "🔐 **Cannot generate blueprint** — Gemini API key is not configured.  \n"
            "Fill in your `GEMINI_API_KEY` in `.env` and restart the application."
        )

    # Render the most recently generated report (persists across reruns)
    if st.session_state.report:
        render_report(st.session_state.report)


if __name__ == "__main__":
    main()
