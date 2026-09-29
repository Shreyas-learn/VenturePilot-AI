"""
rag/rag_pipeline.py — RAG pipeline initialisation entry point.

This module is the single public interface between the application and the
RAG subsystem. All other application code calls only this module — never
document_loader, vector_store, or retriever directly.

Responsibilities:
    - Orchestrate the document loading → embedding → indexing pipeline
    - Return a status summary for display in the UI
    - Handle all RAG failures gracefully so the app never crashes
    - Provide a helper to check whether the knowledge base is available

Typical call sequence (from app.py):
    status = init_rag()          # called once at startup
    context = get_context(...)   # called per Gemini request
"""

import logging
from dataclasses import dataclass

from rag.document_loader import load_documents, scan_knowledge_base
from rag.vector_store import index_documents, get_indexed_hashes, get_document_count
from rag.retriever import retrieve_context_for_template

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RAGStatus:
    """Snapshot of the RAG pipeline state after initialisation.

    Attributes:
        pdf_files_found:    Total PDF files discovered in the knowledge base.
        new_files_indexed:  Number of previously unseen files indexed this run.
        total_chunks:       Total document chunks in the vector store.
        is_available:       True when at least one chunk is indexed.
        embedding_provider: Name of the active embedding provider.
        error:              Error message if initialisation failed, else None.
    """

    pdf_files_found: int
    new_files_indexed: int
    total_chunks: int
    is_available: bool
    embedding_provider: str
    error: str | None = None


def init_rag() -> RAGStatus:
    """Initialise the RAG pipeline at application startup.

    Scans the knowledge base, loads and indexes any new or changed PDFs,
    and returns a status summary.  Always succeeds — any internal error is
    caught and reflected in the returned status object so the application
    can continue without RAG.

    Returns:
        A :class:`RAGStatus` describing the current state of the pipeline.
    """
    logger.info("Initialising RAG pipeline…")

    try:
        # 1. Discover PDF files
        pdf_files = scan_knowledge_base()
        pdf_count = len(pdf_files)

        if pdf_count == 0:
            logger.info("Knowledge base is empty — RAG pipeline inactive.")
            return RAGStatus(
                pdf_files_found=0,
                new_files_indexed=0,
                total_chunks=0,
                is_available=False,
                embedding_provider="n/a",
            )

        # 2. Retrieve hashes of already-indexed files
        known_hashes = get_indexed_hashes()
        logger.info(
            "Knowledge base: %d PDF(s) found, %d file hash(es) already indexed.",
            pdf_count,
            len(known_hashes),
        )

        # 3. Load and chunk only new / changed files
        new_chunks = load_documents(known_hashes=known_hashes)
        new_files = len({c["file_hash"] for c in new_chunks}) if new_chunks else 0

        # 4. Index the new chunks
        if new_chunks:
            index_documents(new_chunks)

        # 5. Resolve the embedding provider name for the status display
        provider = _resolve_embedding_provider()
        total = get_document_count()

        logger.info(
            "RAG pipeline ready — %d chunk(s) indexed, provider: %s.",
            total,
            provider,
        )
        return RAGStatus(
            pdf_files_found=pdf_count,
            new_files_indexed=new_files,
            total_chunks=total,
            is_available=total > 0,
            embedding_provider=provider,
        )

    except Exception as exc:
        logger.error("RAG pipeline initialisation failed: %s", exc, exc_info=True)
        return RAGStatus(
            pdf_files_found=0,
            new_files_indexed=0,
            total_chunks=get_document_count(),
            is_available=get_document_count() > 0,
            embedding_provider="unknown",
            error=str(exc),
        )


def get_context(
    template_name: str,
    startup_name: str,
    industry: str,
    country: str,
    startup_idea: str,
) -> str:
    """Retrieve relevant knowledge base context for a prompt template.

    Returns an empty string when the knowledge base is empty or any
    retrieval error occurs, allowing the caller to proceed without context.

    Args:
        template_name: Prompt template filename (e.g. ``"funding.md"``).
        startup_name:  Name of the startup.
        industry:      Industry vertical.
        country:       Country of operation.
        startup_idea:  Startup idea description.

    Returns:
        Formatted context string, or empty string.
    """
    try:
        return retrieve_context_for_template(
            template_name=template_name,
            startup_name=startup_name,
            industry=industry,
            country=country,
            startup_idea=startup_idea,
        )
    except Exception as exc:
        logger.warning("get_context failed for '%s': %s", template_name, exc)
        return ""


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _resolve_embedding_provider() -> str:
    """Return the active embedding provider label from the EmbeddingManager.

    Reads the already-cached manager singleton so no additional probing
    or initialisation occurs here.

    Returns:
        Human-readable provider name string, or a fallback label on error.
    """
    try:
        from rag.vector_store import get_embedding_manager
        return get_embedding_manager().provider_label
    except Exception as exc:
        logger.debug("Could not resolve embedding provider label: %s", exc)
        return "sentence-transformers (all-MiniLM-L6-v2)"
