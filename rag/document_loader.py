"""
rag/document_loader.py — PDF ingestion, chunking, and change detection.

Responsibilities:
    - Recursively scan the entire knowledge_base directory for PDF files
    - Detect new or modified files using SHA-256 content hashing
    - Extract text from PDFs using pypdf
    - Split extracted text into overlapping chunks with metadata
    - Skip files that are already indexed (idempotent on re-runs)

Chunking parameters (chunk_size, chunk_overlap) are read from
:data:`config.settings.settings` so they are tunable via .env.

Chunk metadata schema:
    {
        "text":      str,   # chunk content
        "source":    str,   # relative file path
        "category":  str,   # subfolder name (e.g. "funding")
        "filename":  str,   # bare filename
        "chunk_id":  int,   # zero-based index within document
        "file_hash": str,   # SHA-256 of file bytes for change detection
    }
"""

import hashlib
import logging
import os

from pypdf import PdfReader
from tqdm import tqdm

from config.settings import settings

logger = logging.getLogger(__name__)

# Chunking parameters sourced from settings (overridable via .env)
def _chunk_size() -> int:
    return settings.rag_chunk_size

def _chunk_overlap() -> int:
    return settings.rag_chunk_overlap


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_knowledge_base() -> list[dict]:
    """Recursively discover all PDF files in the knowledge base.

    Walks the entire ``knowledge_base/`` directory tree. Any subfolder
    name is accepted — not just the predefined category list — so users
    can organise their documents freely.

    Returns:
        List of file-info dicts with keys: ``path``, ``category``, ``filename``.
        Returns an empty list when the directory does not exist or contains no PDFs.
    """
    base = settings.knowledge_base_path

    if not os.path.isdir(base):
        logger.warning(
            "Knowledge base directory not found: '%s'. RAG will be skipped.", base
        )
        return []

    found: list[dict] = []

    for root, _dirs, files in os.walk(base):
        for filename in sorted(files):
            if not filename.lower().endswith(".pdf"):
                continue
            full_path = os.path.join(root, filename)
            # Derive category from the immediate parent folder name
            category = os.path.basename(root) if root != base else "general"
            found.append(
                {
                    "path": full_path,
                    "category": category,
                    "filename": filename,
                }
            )

    logger.info(
        "Knowledge base scan complete — found %d PDF file(s) across all subfolders.",
        len(found),
    )
    return found


def compute_file_hash(path: str) -> str:
    """Return the SHA-256 hex digest of a file's contents.

    Used to detect whether an already-indexed file has been modified.

    Args:
        path: Path to the file.

    Returns:
        64-character hex string.
    """
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def load_documents(known_hashes: set[str] | None = None) -> list[dict]:
    """Load, chunk, and return all new or changed PDF documents.

    Args:
        known_hashes: Set of file hashes already present in the vector store.
                      Chunks from files whose hash is in this set are skipped,
                      making the function idempotent across re-runs.
                      Pass ``None`` or an empty set to load everything.

    Returns:
        A flat list of chunk dicts ready for embedding and indexing.
        Returns an empty list when the knowledge base contains no PDFs.
    """
    known_hashes = known_hashes or set()
    pdf_files = scan_knowledge_base()

    if not pdf_files:
        logger.info("Knowledge base is empty — RAG indexing skipped.")
        return []

    all_chunks: list[dict] = []
    skipped = 0

    for file_info in tqdm(pdf_files, desc="Indexing knowledge base", unit="file"):
        path = file_info["path"]
        file_hash = compute_file_hash(path)

        if file_hash in known_hashes:
            logger.debug("Skipping already-indexed file: %s", file_info["filename"])
            skipped += 1
            continue

        try:
            chunks = _extract_and_chunk(
                path=path,
                category=file_info["category"],
                filename=file_info["filename"],
                file_hash=file_hash,
            )
            all_chunks.extend(chunks)
            logger.info(
                "Loaded '%s' → %d chunks (category: %s)",
                file_info["filename"],
                len(chunks),
                file_info["category"],
            )
        except Exception as exc:
            logger.warning(
                "Failed to load '%s': %s — skipping.", file_info["filename"], exc
            )

    logger.info(
        "Document loading complete — %d new chunks from %d file(s) (%d skipped).",
        len(all_chunks),
        len(pdf_files) - skipped,
        skipped,
    )
    return all_chunks


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_and_chunk(
    path: str,
    category: str,
    filename: str,
    file_hash: str,
) -> list[dict]:
    """Extract text from a PDF and split it into overlapping chunks.

    Args:
        path:      Full path to the PDF file.
        category:  Knowledge base category (parent folder name).
        filename:  Bare filename for metadata.
        file_hash: SHA-256 digest of the file for change tracking.

    Returns:
        List of chunk dicts with all metadata populated.
    """
    reader = PdfReader(path)
    pages_text: list[str] = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text and page_text.strip():
            pages_text.append(page_text.strip())

    full_text = "\n\n".join(pages_text)

    if not full_text.strip():
        logger.warning("No extractable text found in '%s' — skipping.", filename)
        return []

    return _chunk_text(
        text=full_text,
        source=path,
        category=category,
        filename=filename,
        file_hash=file_hash,
    )


def _chunk_text(
    text: str,
    source: str,
    category: str,
    filename: str,
    file_hash: str,
) -> list[dict]:
    """Split text into overlapping fixed-size character chunks.

    Respects sentence boundaries by preferring to break at the last
    period or newline within the chunk window.

    Args:
        text:      Full document text.
        source:    File path (for metadata).
        category:  Document category (for metadata).
        filename:  Bare filename (for metadata).
        file_hash: File hash (for change detection metadata).

    Returns:
        List of chunk dicts.
    """
    chunk_size    = _chunk_size()
    chunk_overlap = _chunk_overlap()

    chunks: list[dict] = []
    text = text.strip()
    start = 0
    chunk_id = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Prefer breaking at a sentence boundary within the window
        if end < len(text):
            boundary = _find_break(text, start, end)
            if boundary:
                end = boundary

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(
                {
                    "text": chunk_text,
                    "source": source,
                    "category": category,
                    "filename": filename,
                    "chunk_id": chunk_id,
                    "file_hash": file_hash,
                }
            )
            chunk_id += 1

        # Advance with overlap
        start = end - chunk_overlap if end < len(text) else end

    return chunks


def _find_break(text: str, start: int, end: int) -> int | None:
    """Find the last sentence-friendly break position in [start, end].

    Searches backward from ``end`` for a period followed by whitespace,
    or a newline. Returns the break position (exclusive), or None when
    no suitable boundary is found.

    Args:
        text:  Full document text.
        start: Chunk start index.
        end:   Chunk end index (exclusive).

    Returns:
        Break position index, or None.
    """
    window = text[start:end]
    # Walk backward from end of window
    for i in range(len(window) - 1, max(len(window) - 200, 0), -1):
        char = window[i]
        if char == "\n":
            return start + i + 1
        if char in ".!?" and i + 1 < len(window) and window[i + 1] in " \n":
            return start + i + 1
    return None
