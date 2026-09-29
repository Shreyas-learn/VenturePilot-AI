"""
_embed_test.py — Embedding pipeline smoke tests for VenturePilot AI (Gemini Edition).

Run from the project root:
    python _embed_test.py

Tests:
    1. Settings loads correctly
    2. GEMINI_API_KEY is detected
    3. EmbeddingManager initialises with sentence-transformers
    4. embed_documents() returns vectors of the right shape
    5. embed_query() returns a single vector
    6. ChromaDB collection is accessible
    7. RAG pipeline status is readable
    8. get_context() returns a string (possibly empty if ChromaDB is empty)
"""

import sys

print("=" * 60)
print("VenturePilot AI — Embedding & RAG smoke test")
print("=" * 60)

# ── 1. Settings ───────────────────────────────────────────────────────────────
from config.settings import settings

assert hasattr(settings, 'gemini_api_key'), "Missing gemini_api_key"
assert hasattr(settings, 'gemini_model'),   "Missing gemini_model"
assert hasattr(settings, 'preferred_embedding_provider'), "Missing preferred_embedding_provider"
print(f"[1] Settings loaded: model='{settings.gemini_model}', "
      f"embedding='{settings.preferred_embedding_provider}' — OK")

# ── 2. GEMINI_API_KEY presence check (not value check) ───────────────────────
if settings.gemini_api_key:
    print(f"[2] GEMINI_API_KEY is set (length={len(settings.gemini_api_key)}) — OK")
else:
    print("[2] GEMINI_API_KEY is NOT set — generation will fail, but RAG tests can continue")

# ── 3. EmbeddingManager initialises ──────────────────────────────────────────
from rag.embedding_manager import EmbeddingManager

manager = EmbeddingManager()
assert manager.provider_label, "provider_label is empty"
assert "sentence-transformers" in manager.provider_label.lower(), \
    f"Expected sentence-transformers, got: {manager.provider_label}"
print(f"[3] EmbeddingManager: provider='{manager.provider_label}' — OK")

# ── 4. embed_documents() ─────────────────────────────────────────────────────
texts = ["startup business plan", "funding opportunities for tech startups"]
vectors = manager.embed_documents(texts)
assert len(vectors) == 2, f"Expected 2 vectors, got {len(vectors)}"
assert len(vectors[0]) > 0, "Vector[0] is empty"
assert len(vectors[1]) > 0, "Vector[1] is empty"
assert len(vectors[0]) == len(vectors[1]), "Vector dimensions don't match"
print(f"[4] embed_documents(): {len(vectors)} vectors × dim={len(vectors[0])} — OK")

# ── 5. embed_query() ─────────────────────────────────────────────────────────
qvec = manager.embed_query("go-to-market strategy for AgriTech in India")
assert len(qvec) > 0, "Query vector is empty"
print(f"[5] embed_query(): dim={len(qvec)} — OK")

# ── 6. ChromaDB collection ───────────────────────────────────────────────────
from rag.vector_store import get_collection, get_document_count

collection = get_collection()
count = get_document_count()
print(f"[6] ChromaDB collection '{collection.name}': {count} chunks indexed — OK")

# ── 7. RAG pipeline status ───────────────────────────────────────────────────
from rag.rag_pipeline import init_rag

status = init_rag()
provider_str = status.embedding_provider
assert "sentence-transformers" in provider_str.lower(), \
    f"Expected sentence-transformers in provider, got: {provider_str}"
print(f"[7] RAG status: pdfs={status.pdf_files_found}, chunks={status.total_chunks}, "
      f"available={status.is_available}, provider='{provider_str}' — OK")

# ── 8. get_context() ─────────────────────────────────────────────────────────
from rag.rag_pipeline import get_context

ctx = get_context(
    template_name="funding.md",
    startup_name="TestStartup",
    industry="AgriTech",
    country="India",
    startup_idea="AI-powered crop monitoring platform for smallholder farmers",
)
assert isinstance(ctx, str), "get_context() must return a string"
if ctx:
    print(f"[8] get_context(): returned {len(ctx)} chars of RAG context — OK")
else:
    print("[8] get_context(): returned empty string (ChromaDB may be empty) — OK")

print()
print("=" * 60)
print("All embedding/RAG tests passed.")
print("=" * 60)
