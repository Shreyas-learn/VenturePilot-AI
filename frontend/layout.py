"""
frontend/layout.py — Page configuration, sidebar, and header rendering.

All global UI chrome lives here so that app.py stays lightweight.
"""

from __future__ import annotations

import streamlit as st

from config.constants import APP_NAME, APP_VERSION, APP_TAGLINE, APP_MOTTO


def configure_page() -> None:
    """Set Streamlit page-level configuration.

    Must be the very first Streamlit call in the application.
    """
    st.set_page_config(
        page_title=f"{APP_NAME} — {APP_TAGLINE}",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        :root {
            --vp-ink: #182820;
            --vp-muted: #5f6d65;
            --vp-paper: #f5f7f5;
            --vp-panel: #ffffff;
            --vp-line: #dbe3dd;
            --vp-green: #176b52;
            --vp-coral: #bd6547;
        }
        [data-testid="stAppViewContainer"] { background: var(--vp-paper); }
        [data-testid="stSidebar"] {
            background: #edf2ee;
            border-right: 1px solid var(--vp-line);
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 1360px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        h1, h2, h3 { color: var(--vp-ink); letter-spacing: 0; }
        h1 { font-family: Georgia, serif; }
        [data-testid="stMetric"] {
            background: var(--vp-panel);
            border: 1px solid var(--vp-line);
            border-radius: 6px;
            padding: 0.65rem 0.8rem;
        }
        div[data-testid="stExpander"] {
            background: var(--vp-panel);
            border: 1px solid var(--vp-line);
            border-radius: 6px;
        }
        .stButton > button[kind="primary"] {
            background: var(--vp-green);
            border-color: var(--vp-green);
        }
        .stButton > button[kind="primary"]:hover {
            background: #10583f;
            border-color: #10583f;
        }
        .vp-header {
            border-bottom: 1px solid var(--vp-line);
            margin-bottom: 1.5rem;
            padding: 0.4rem 0 1.35rem;
            animation: vp-enter 420ms ease-out both;
        }
        .vp-header h1 {
            font-family: Georgia, serif;
            font-size: 2.4rem;
            font-weight: 700;
            line-height: 1.15;
            margin: 0.35rem 0 0.3rem;
        }
        .vp-eyebrow {
            color: var(--vp-green);
            font-size: 0.75rem;
            font-weight: 700;
        }
        .vp-tagline { color: var(--vp-ink); font-size: 1.05rem; margin: 0; }
        .vp-motto { color: var(--vp-coral); font-size: 0.88rem; margin: 0.3rem 0 0; }
        @keyframes vp-enter {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @media (prefers-reduced-motion: reduce) {
            .vp-header { animation: none; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Render the branded hero header at the top of the main content area."""
    st.markdown(
        f"""
        <div class="vp-header">
            <div class="vp-eyebrow">VENTUREPILOT / STARTUP STRATEGY</div>
            <h1>{APP_NAME}</h1>
            <p class="vp-tagline">{APP_TAGLINE}</p>
            <p class="vp-motto">{APP_MOTTO}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(rag_status=None) -> None:
    """Render the application sidebar with branding, metadata, and RAG status.

    Args:
        rag_status: Optional :class:`rag.rag_pipeline.RAGStatus` instance.
                    When provided, displays knowledge base statistics.
    """
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 1rem 0;">
                <h2 style="font-size: 1.5rem; font-weight: 800; margin-bottom: 0;">
                    🚀 {APP_NAME}
                </h2>
                <p style="color: #57606a; font-size: 0.85rem; margin-top: 0.2rem;">
                    {APP_MOTTO}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        st.markdown("### About")
        st.markdown(
            "VenturePilot AI is an **AI Startup Consultant** that transforms "
            "your startup idea into an investor-ready business blueprint."
        )

        st.divider()

        st.markdown("### Technologies")
        st.markdown(
            "- 🤖 **Google Gemini** — Foundation LLM\n"
            "- 🔍 **RAG Pipeline** — Knowledge retrieval\n"
            "- 🗄️ **ChromaDB** — Vector store\n"
            "- 📐 **sentence-transformers** — Embeddings\n"
            "- 🌐 **Streamlit** — Web interface"
        )

        st.divider()

        _render_rag_status(rag_status)

        st.divider()

        st.caption(f"Version {APP_VERSION}")


def _render_rag_status(rag_status) -> None:
    """Render knowledge base status indicators in the sidebar.

    Args:
        rag_status: :class:`rag.rag_pipeline.RAGStatus` or None.
    """
    st.markdown("### 📚 Knowledge Base")

    if rag_status is None:
        st.caption("Initialising…")
        return

    if rag_status.error:
        st.warning(f"⚠️ RAG error: {rag_status.error}", icon="⚠️")

    if not rag_status.is_available:
        st.info(
            "No documents indexed yet.  \n"
            "Add PDFs to `knowledge_base/` subfolders to enable "
            "knowledge-enhanced responses.",
            icon="ℹ️",
        )
        return

    # Show a compact metrics row
    col1, col2 = st.columns(2)
    col1.metric("PDF Files", rag_status.pdf_files_found)
    col2.metric("Chunks", rag_status.total_chunks)

    if rag_status.new_files_indexed > 0:
        st.success(
            f"✅ {rag_status.new_files_indexed} new file(s) indexed this session.",
            icon="✅",
        )
    else:
        st.success("✅ Knowledge base up to date.", icon="✅")

    _render_embedding_provider(rag_status.embedding_provider)


def _render_embedding_provider(provider_label: str) -> None:
    """Render the embedding provider indicator with a colour-coded status icon.

    🟢 = sentence-transformers (primary, local)

    Args:
        provider_label: The :attr:`~rag.embedding_manager.EmbeddingManager.provider_label`
                        string from the active manager instance.
    """
    st.markdown(
        f"**Embedding Provider:**  \n🟢 {provider_label}"
    )
