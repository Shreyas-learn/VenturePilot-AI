"""
rag/vector_store.py — ChromaDB vector store management.

Responsibilities:
    - Provide a cached ChromaDB client and collection handle
    - Delegate all embedding to :class:`rag.embedding_manager.EmbeddingManager`
    - Index new document chunks idempotently (hash-based deduplication)
    - Expose indexed file hashes for change detection
    - Provide a document count for UI status display

Embedding strategy is owned entirely by EmbeddingManager — this module
has no knowledge of which provider is active.
"""

import logging
import os
from functools import lru_cache

import chromadb

from config.settings import settings

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "venture_pilot_kb"


# ---------------------------------------------------------------------------
# Singletons — client and embedding manager are created once per process
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_chroma_client() -> chromadb.PersistentClient:
    """Return the singleton ChromaDB persistent client.

    Created once per process. The persistence directory is created
    automatically when absent.

    Returns:
        A :class:`~chromadb.PersistentClient` instance.
    """
    os.makedirs(settings.chroma_db_path, exist_ok=True)
    client = chromadb.PersistentClient(path=settings.chroma_db_path)
    logger.debug("ChromaDB client ready at '%s'.", settings.chroma_db_path)
    return client


@lru_cache(maxsize=1)
def get_embedding_manager():
    """Return the singleton :class:`~rag.embedding_manager.EmbeddingManager`.

    Resolves the active embedding provider once and caches the result
    for the process lifetime.

    Returns:
        An initialised :class:`~rag.embedding_manager.EmbeddingManager`.
    """
    from rag.embedding_manager import EmbeddingManager
    return EmbeddingManager()


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------

def get_collection() -> chromadb.Collection:
    """Return the ChromaDB collection, creating it if absent.

    The collection uses cosine similarity. The embedding function is
    provided by :func:`get_embedding_manager` and remains constant for
    the process lifetime.

    Returns:
        A ChromaDB :class:`~chromadb.Collection` instance.
    """
    client  = _get_chroma_client()
    manager = get_embedding_manager()

    collection = client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=manager,   # EmbeddingManager IS an EmbeddingFunction
        metadata={"hnsw:space": "cosine"},
    )
    logger.debug(
        "Collection '%s' ready — %d chunk(s) indexed, provider: %s.",
        _COLLECTION_NAME,
        collection.count(),
        manager.provider_label,
    )
    return collection


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

def get_indexed_hashes() -> set[str]:
    """Return SHA-256 hashes of files already present in the vector store.

    Used by the document loader to skip unchanged files on re-runs,
    making the indexing pipeline idempotent.

    Returns:
        Set of hex-digest strings, or an empty set on any error.
    """
    try:
        collection = get_collection()
        if collection.count() == 0:
            return set()
        results = collection.get(include=["metadatas"])
        hashes: set[str] = set()
        for meta in results.get("metadatas") or []:
            if meta and "file_hash" in meta:
                hashes.add(meta["file_hash"])
        return hashes
    except Exception as exc:
        logger.warning("Could not retrieve indexed hashes: %s", exc)
        return set()


def index_documents(chunks: list[dict]) -> None:
    """Add document chunks to the vector store (idempotent).

    Chunks whose ID already exists in the collection are silently skipped,
    so this function is safe to call multiple times.

    Args:
        chunks: List of chunk dicts produced by
                :func:`rag.document_loader.load_documents`.
    """
    if not chunks:
        logger.info("No new chunks to index.")
        return

    collection = get_collection()

    existing_ids: set[str] = set(collection.get(include=[])["ids"])
    new_chunks = [c for c in chunks if _chunk_id(c) not in existing_ids]

    if not new_chunks:
        logger.info("All chunks are already indexed — no action needed.")
        return

    _batch_add(collection, new_chunks)
    logger.info(
        "Indexed %d new chunk(s) into '%s' (%d total).",
        len(new_chunks),
        _COLLECTION_NAME,
        collection.count(),
    )


def get_document_count() -> int:
    """Return the total number of indexed document chunks.

    Returns:
        Integer count, or 0 on any error.
    """
    try:
        return get_collection().count()
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _batch_add(
    collection: chromadb.Collection,
    chunks: list[dict],
    batch_size: int = 100,
) -> None:
    """Insert chunks into ChromaDB in fixed-size batches.

    Args:
        collection: Target collection.
        chunks:     Chunks to insert.
        batch_size: Maximum documents per API call (default: 100).
    """
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.add(
            ids=[_chunk_id(c) for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[
                {
                    "source":    c["source"],
                    "category":  c["category"],
                    "filename":  c.get("filename", ""),
                    "file_hash": c.get("file_hash", ""),
                }
                for c in batch
            ],
        )
        logger.debug("Batch inserted %d chunk(s) (offset %d).", len(batch), i)


def _chunk_id(chunk: dict) -> str:
    """Return a stable, unique ID for a chunk within the collection.

    Args:
        chunk: Chunk dict with ``file_hash`` and ``chunk_id`` keys.

    Returns:
        String ID in the form ``<file_hash>::<chunk_id>``.
    """
    file_hash = chunk.get("file_hash", chunk["source"])
    return f"{file_hash}::{chunk['chunk_id']}"
