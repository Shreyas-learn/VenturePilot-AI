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


def render_header() -> None:
    """Render the branded hero header at the top of the main content area."""
    st.markdown(
        f"""
        <div style="text-align: center; padding: 2rem 0 1rem 0;">
            <h1 style="font-size: 2.8rem; font-weight: 800; margin-bottom: 0.1rem;">
                🚀 {APP_NAME}
            </h1>
            <p style="font-size: 1.15rem; color: #57606a; margin-top: 0.25rem;">
                {APP_TAGLINE} &nbsp;|&nbsp; <em>{APP_MOTTO}</em>
            </p>
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
