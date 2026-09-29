"""
rag/retriever.py — Semantic context retrieval for prompt augmentation.

Responsibilities:
    - Accept a natural-language query string
    - Search the ChromaDB collection for the most relevant chunks
    - Return a formatted context block ready for injection into a prompt
    - Degrade gracefully when the collection is empty or unavailable

Each prompt template queries with a domain-specific string so that the
retrieved context is relevant to the sections being generated.
"""

import logging

from rag.vector_store import get_collection

logger = logging.getLogger(__name__)


def retrieve_context(query: str, top_k: int | None = None) -> str:
    """Retrieve the most relevant knowledge base passages for a query.

    Queries ChromaDB using cosine similarity. Returns an empty string
    when the collection is empty, the query returns no results, or any
    error occurs — allowing the application to continue without RAG.

    Args:
        query:  Natural-language query string derived from the startup input
                and the domain of the sections being generated.
        top_k:  Maximum number of passages to retrieve.

    Returns:
        A formatted multi-passage context string ready for prompt injection,
        or an empty string when no relevant context is available.
    """
    from config.settings import settings  # local import avoids circular dep at module level

    effective_top_k   = top_k if top_k is not None else settings.rag_top_k
    threshold         = settings.rag_similarity_threshold

    try:
        collection = get_collection()
        count = collection.count()

        if count == 0:
            logger.info("Knowledge base is empty — RAG retrieval skipped.")
            return ""

        n_results = min(effective_top_k, count)
        logger.debug(
            "Querying ChromaDB — query='%s...', top_k=%d, collection_size=%d",
            query[:60],
            n_results,
            count,
        )

        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        passages  = results.get("documents",  [[]])[0]
        metadatas = results.get("metadatas",  [[]])[0]
        distances = results.get("distances",  [[]])[0]

        if not passages:
            logger.info("No relevant passages found for query.")
            return ""

        # Filter out passages below the configured relevance threshold
        relevant = [
            (p, m, d)
            for p, m, d in zip(passages, metadatas, distances)
            if d <= threshold
        ]

        if not relevant:
            logger.info(
                "All retrieved passages exceeded similarity threshold (%.2f) — skipping.",
                threshold,
            )
            return ""

        logger.info(
            "Retrieved %d relevant passage(s) from knowledge base (of %d candidates).",
            len(relevant),
            n_results,
        )
        return _format_context(relevant)

    except Exception as exc:
        logger.warning(
            "RAG retrieval failed: %s — continuing without context.", exc
        )
        return ""


def retrieve_context_for_template(
    template_name: str,
    startup_name: str,
    industry: str,
    country: str,
    startup_idea: str,
) -> str:
    """Build a domain-specific query for a prompt template and retrieve context.

    Each template targets a different domain. Using a specific query for
    each domain yields more relevant passages than a single generic query.

    Args:
        template_name: The prompt template filename (e.g. ``"funding.md"``).
        startup_name:  Name of the startup.
        industry:      Industry vertical.
        country:       Country of operation.
        startup_idea:  Brief description of the startup idea.

    Returns:
        A formatted context string, or an empty string when not applicable.
    """
    query = _build_query(
        template_name=template_name,
        startup_name=startup_name,
        industry=industry,
        country=country,
        startup_idea=startup_idea,
    )

    logger.debug("RAG query for '%s': %s", template_name, query[:80])
    return retrieve_context(query)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

_TEMPLATE_QUERY_PREFIXES: dict[str, str] = {
    "business_blueprint.md": (
        "business model canvas, value proposition, executive summary, "
        "startup strategy, revenue streams"
    ),
    "market_analysis.md": (
        "competitor analysis, market research, SWOT analysis, "
        "go-to-market strategy, market size"
    ),
    "funding.md": (
        "startup funding, government schemes, DPIIT recognition, "
        "Startup India Seed Fund, MSME, SIDBI, incubators, venture capital"
    ),
    "startup_score.md": (
        "startup roadmap, execution milestones, risks, product development, "
        "investor readiness, startup evaluation"
    ),
    "investor_pitch.md": (
        "investor pitch deck, elevator pitch, startup recommendation, "
        "funding ask, investment thesis"
    ),
}


def _build_query(
    template_name: str,
    startup_name: str,
    industry: str,
    country: str,
    startup_idea: str,
) -> str:
    """Construct a retrieval query tailored to the template domain.

    Args:
        template_name: Prompt template filename.
        startup_name:  Startup name.
        industry:      Industry vertical.
        country:       Country.
        startup_idea:  Startup idea description (truncated to 200 chars).

    Returns:
        A natural-language query string.
    """
    domain_prefix = _TEMPLATE_QUERY_PREFIXES.get(
        template_name,
        "startup business advice",
    )
    idea_snippet = startup_idea[:200].strip()

    return (
        f"{domain_prefix} for a {industry} startup in {country}. "
        f"Startup: {startup_name}. Idea: {idea_snippet}"
    )


def _format_context(
    relevant: list[tuple[str, dict, float]],
) -> str:
    """Format retrieved passages into a prompt-ready context block.

    Truncates the total context to settings.rag_max_context_chars to
    prevent oversized prompts from exceeding model token limits.

    Args:
        relevant: List of (passage, metadata, distance) tuples.

    Returns:
        A formatted context string.
    """
    from config.settings import settings

    max_chars = settings.rag_max_context_chars
    lines: list[str] = ["[KNOWLEDGE BASE CONTEXT]"]
    total_chars = 0

    for i, (passage, meta, distance) in enumerate(relevant, start=1):
        filename = meta.get("filename") or meta.get("source", "unknown")
        category = meta.get("category", "")
        relevance = round((1 - distance) * 100, 1)

        header = f"\n[{i}] {filename} ({category}) — relevance: {relevance}%"
        entry = f"{header}\n{passage}"

        if total_chars + len(entry) > max_chars:
            # Include a truncated version of the last passage if there's room
            remaining = max_chars - total_chars - len(header) - 20
            if remaining > 100:
                lines.append(f"{header}\n{passage[:remaining]}…")
            break

        lines.append(entry)
        total_chars += len(entry)

    lines.append("\n[END CONTEXT]")
    return "\n".join(lines)
