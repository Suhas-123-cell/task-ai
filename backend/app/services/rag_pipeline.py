"""
Retrieval-Augmented Generation pipeline: chunking, embedding, vector
storage, and retrieval.

Design decisions (assignment section 6, "AI/ML Requirements"):

Chunking strategy -- sentence-boundary-snapped sliding window, not a fixed
hard cut. A pure fixed-size cut (e.g. every 900 characters no matter what)
will regularly slice a sentence in half, which both damages embedding
quality (the embedding model sees a syntactically broken fragment) and
damages the retrieved context handed to the question generator (a
half-sentence is a worse grounding source than a complete one). Instead,
each chunk's boundary is snapped forward to the next sentence-ending
period within a small lookahead window, so chunks are close to the target
size but end on a complete thought.

Context preservation -- consecutive chunks overlap by `chunk_overlap_chars`
characters. Without overlap, a concept explained across a chunk boundary
(e.g. "Entropy is defined as X. | Information gain then uses this to...")
would have its two halves embedded and retrieved completely independently,
losing the connective context. Overlap trades a small amount of storage
duplication for much better continuity.

Retrieval efficiency -- embeddings are generated once at ingestion time and
persisted in a local Chroma collection (one collection per role), so a
query at interview time is a single approximate-nearest-neighbor lookup
rather than an embed-and-compare-everything scan. A local, embedded
sentence-transformers model (all-MiniLM-L6-v2, 384-dim) is used instead of
a hosted embedding API: embeddings are needed at both ingestion and
query time on every request, so keeping that hot path free of network
latency and API cost/rate limits matters more than the marginal quality
gain of a larger hosted embedding model.
"""
import os
import re
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.config import KNOWLEDGE_BASE_DIR, get_settings

settings = get_settings()

_SENTENCE_BOUNDARY_RE = re.compile(r"[.!?]\s")
_LOOKAHEAD_WINDOW = 200

_embedding_model: SentenceTransformer | None = None
_chroma_client: chromadb.ClientAPI | None = None


def get_embedding_model() -> SentenceTransformer:
    # Plain lazy singleton, no lock: uvicorn's dev/single-worker setup used here never
    # calls this from more than one thread before the first request completes warmup,
    # and the worst case of a lost race (loading the model twice) is a one-time memory
    # blip, not a correctness issue -- double-checked locking was speculative hardening
    # for a concurrency scenario this deployment doesn't have (ponytail-review flagged
    # this as premature; simplified per that review).
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(settings.embedding_model)
    return _embedding_model


def get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def _collection_name(role: str) -> str:
    return f"kb_{role}"


def get_collection(role: str):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=_collection_name(role), metadata={"hnsw:space": "cosine"}
    )


@dataclass
class Chunk:
    text: str
    source_file: str
    chunk_index: int


def chunk_text(text: str, source_file: str, chunk_size: int, overlap: int) -> list[Chunk]:
    """Sentence-boundary-snapped sliding window chunker. See module docstring."""
    text = text.strip()
    chunks: list[Chunk] = []
    start = 0
    chunk_index = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)
        if end < n:
            lookahead_end = min(end + _LOOKAHEAD_WINDOW, n)
            window = text[end:lookahead_end]
            match = _SENTENCE_BOUNDARY_RE.search(window)
            if match:
                end = end + match.end()

        chunk_str = text[start:end].strip()
        if chunk_str:
            chunks.append(Chunk(text=chunk_str, source_file=source_file, chunk_index=chunk_index))
            chunk_index += 1

        if end >= n:
            break
        start = max(end - overlap, start + 1)

    return chunks


def load_role_documents(role: str) -> list[tuple[str, str]]:
    """Return (filename, raw_text) for every supported document under a role's KB dir."""
    role_dir = KNOWLEDGE_BASE_DIR / role
    if not role_dir.exists():
        raise ValueError(f"No knowledge base directory found for role '{role}'")

    documents = []
    for path in sorted(role_dir.glob("*")):
        if path.suffix.lower() in (".md", ".txt"):
            documents.append((path.name, path.read_text(encoding="utf-8")))
        elif path.suffix.lower() == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            text = "\n".join((p.extract_text() or "") for p in reader.pages)
            documents.append((path.name, text))
    return documents


def ingest_role(role: str) -> int:
    """Chunk + embed + store every document for a role. Returns chunk count. Idempotent."""
    documents = load_role_documents(role)
    collection = get_collection(role)

    all_chunks: list[Chunk] = []
    for filename, text in documents:
        all_chunks.extend(
            chunk_text(text, filename, settings.chunk_size_chars, settings.chunk_overlap_chars)
        )

    if not all_chunks:
        return 0

    model = get_embedding_model()
    embeddings = model.encode([c.text for c in all_chunks], show_progress_bar=False).tolist()

    ids = [f"{role}::{c.source_file}::{c.chunk_index}" for c in all_chunks]
    metadatas = [{"source_file": c.source_file, "chunk_index": c.chunk_index, "role": role} for c in all_chunks]
    documents_text = [c.text for c in all_chunks]

    # upsert (not add) so re-running ingestion after editing a KB file is safe and idempotent
    collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents_text)
    return len(all_chunks)


def retrieve(role: str, query: str, top_k: int | None = None) -> list[dict]:
    """Embed `query` and return the top_k most relevant chunks for `role`."""
    top_k = top_k or settings.retrieval_top_k
    collection = get_collection(role)
    if collection.count() == 0:
        return []

    model = get_embedding_model()
    query_embedding = model.encode([query], show_progress_bar=False).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    for text, metadata, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        retrieved.append(
            {
                "text": text,
                "source_file": metadata.get("source_file"),
                "chunk_index": metadata.get("chunk_index"),
                # cosine distance -> similarity score in [0, 1], higher is more relevant
                "similarity_score": round(1 - distance, 4),
            }
        )
    return retrieved
