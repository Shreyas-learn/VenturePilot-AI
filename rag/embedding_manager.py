"""
rag/embedding_manager.py — Embedding provider using sentence-transformers.

This is the single source of truth for all embedding operations in the
RAG pipeline.  No other module deals with embedding providers directly.

Strategy:

    Uses sentence-transformers (all-MiniLM-L6-v2) as the embedding model.
    This is a local model — no external API key required.
    The embedding provider is completely independent from the generation LLM.

    Generation LLM:  Google Gemini  (via gemini/gemini_client.py)
    Embedding model: sentence-transformers all-MiniLM-L6-v2  (local)

Public interface (used by vector_store.py):

    manager = EmbeddingManager()
    vectors = manager.embed_documents(["text1", "text2"])
    vector  = manager.embed_query("query text")
    label   = manager.provider_label   # human-readable name for the UI

ChromaDB integration:

    EmbeddingManager also implements the ChromaDB EmbeddingFunction protocol
    so it can be passed directly to ``client.get_or_create_collection()``.
"""

import logging
from typing import List

from chromadb import EmbeddingFunction, Documents, Embeddings

logger = logging.getLogger(__name__)


class EmbeddingManager(EmbeddingFunction[Documents]):
    """Sentence-transformers embedding interface, ChromaDB-compatible.

    Implements the ChromaDB :class:`EmbeddingFunction` protocol so it can be
    passed directly to ChromaDB without any adapter layer.

    Attributes:
        provider_label: Human-readable name of the active provider.
        using_ibm:      Always False — kept for interface compatibility.
    """

    def __init__(self) -> None:
        self._init_sentence_transformers()

    # ------------------------------------------------------------------
    # ChromaDB EmbeddingFunction protocol
    # ------------------------------------------------------------------

    def __call__(self, input: Documents) -> Embeddings:  # type: ignore[override]
        """Embed a list of documents (ChromaDB protocol entry point).

        Args:
            input: List of text strings to embed.

        Returns:
            List of embedding vectors.
        """
        return self.embed_documents(list(input))  # type: ignore[return-value]

    @staticmethod
    def name() -> str:
        return "venture_pilot_embedding_manager"

    @staticmethod
    def build_from_config(config: dict) -> "EmbeddingManager":
        return EmbeddingManager()

    def get_config(self) -> dict:
        return {"provider": self.provider_label}

    # ------------------------------------------------------------------
    # Public embedding interface
    # ------------------------------------------------------------------

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of document strings.

        Args:
            texts: Non-empty list of text strings.

        Returns:
            Parallel list of embedding vectors.
        """
        return self._embed_fn(texts)  # type: ignore[return-value]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string.

        Args:
            text: Query string.

        Returns:
            Single embedding vector.
        """
        if hasattr(self._embed_fn, "embed_query"):
            return self._embed_fn.embed_query([text])[0]  # type: ignore[return-value]
        result = self._embed_fn([text])
        return result[0]  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_sentence_transformers(self) -> None:
        """Initialise the sentence-transformers embedding function."""
        from chromadb.utils.embedding_functions import (
            SentenceTransformerEmbeddingFunction,
        )

        st_fn = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self._embed_fn = st_fn
        self.provider_label = "sentence-transformers (all-MiniLM-L6-v2)"
        self.using_ibm = False

        logger.info(
            "Embedding provider: sentence-transformers (all-MiniLM-L6-v2)."
        )
