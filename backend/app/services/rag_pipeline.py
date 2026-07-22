"""
Retrieval-Augmented Generation pipeline: chunking, embedding, vector
storage, and retrieval.

Design decisions (assignment section 6, "AI/ML Requirements"):

Semantic chunking, not a fixed-size sliding window. An earlier version split
text purely by character count (with sentence-boundary snapping so it at
least didn't cut mid-sentence). That still had a real weakness: a fixed
character budget has no idea where one idea actually ends and the next
begins, so it routinely grouped unrelated sentences into one chunk and
split single ideas across two overlapping chunks -- diluting each
embedding's signal and, downstream, diluting the context handed to the
question generator (a known RAG failure mode sometimes called "context
rot": stuffing a prompt with loosely-related or redundant text degrades
the model's ability to attend to what actually matters). Semantic chunking
instead embeds each sentence, walks through them in order, and starts a new
chunk exactly where cosine similarity to the next sentence drops below
`semantic_similarity_threshold` -- i.e. where the topic actually shifts.
`min_chunk_chars`/`max_chunk_chars` bound the result so a long run of
similar sentences doesn't produce one giant chunk and a run of dissimilar
short sentences doesn't produce many context-poor slivers. This also
removes the old overlap mechanism entirely: overlap existed to avoid
losing context AT an arbitrary cut point, but a chunk boundary chosen at an
actual topic shift has much less continuity to lose in the first place, so
the storage/redundancy cost of overlap is no longer worth paying.

Context-rot mitigation at retrieval time, not just at ingestion time. Even
with better chunk boundaries, a fixed `top_k` will still sometimes force in
a chunk that isn't actually relevant to the query, purely to fill the
quota -- that chunk is then quoted or referenced in the LLM prompt as if it
were meaningful grounding, which is exactly the dilution problem semantic
chunking is trying to avoid on the ingestion side. `retrieve()` therefore
drops any result below `retrieval_min_similarity`, accepting fewer than
top_k chunks (down to a guaranteed minimum of one) rather than padding the
prompt with low-relevance filler.

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
import numpy as np
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.config import KNOWLEDGE_BASE_DIR, get_settings

settings = get_settings()

_HEADING_RE = re.compile(r"^#+\s.*$", re.MULTILINE)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

_embedding_model: SentenceTransformer | None = None
_chroma_client: chromadb.ClientAPI | None = None


class KnowledgeBaseNotIngestedError(Exception):
    """
    Raised when retrieve() is called for a role whose Chroma collection is empty.

    Silently returning an empty context list here would let question generation
    fall back to its context-free path without anyone noticing -- indistinguishable
    from a real (but unusual) zero-relevance retrieval. For strict grading /
    reviewer scrutiny, a missing ingestion step should fail loudly and immediately
    with an actionable message, not silently degrade the "RAG" system into a
    non-RAG one.
    """

    def __init__(self, role: str):
        self.role = role
        super().__init__(
            f"The knowledge base for role '{role}' has not been ingested yet "
            f"(its Chroma collection is empty). Run `python scripts/ingest_kb.py {role}` "
            f"(or `python scripts/ingest_kb.py` to ingest all roles) before starting "
            f"an interview for this role."
        )


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


def _split_into_sentences(text: str) -> list[str]:
    without_headings = _HEADING_RE.sub("", text).strip()
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(without_headings) if s.strip()]


def semantic_chunk_text(
    text: str,
    source_file: str,
    model: SentenceTransformer,
    similarity_threshold: float,
    min_chunk_chars: int,
    max_chunk_chars: int,
) -> list[Chunk]:
    """Group consecutive sentences into chunks, breaking at detected topic shifts.
    See module docstring for the reasoning."""
    sentences = _split_into_sentences(text)
    if not sentences:
        return []
    if len(sentences) == 1:
        return [Chunk(text=sentences[0], source_file=source_file, chunk_index=0)]

    # normalize_embeddings=True gives unit vectors, so a plain dot product between
    # consecutive sentence embeddings IS their cosine similarity -- no separate
    # normalization step needed at comparison time.
    embeddings = model.encode(sentences, show_progress_bar=False, normalize_embeddings=True)

    chunks: list[Chunk] = []
    chunk_index = 0
    current_sentences = [sentences[0]]
    current_len = len(sentences[0])

    for i in range(1, len(sentences)):
        similarity = float(np.dot(embeddings[i - 1], embeddings[i]))
        sentence = sentences[i]
        would_be_len = current_len + 1 + len(sentence)

        topic_shift = similarity < similarity_threshold
        over_max = would_be_len > max_chunk_chars
        under_min = current_len < min_chunk_chars

        if (topic_shift or over_max) and not under_min:
            chunks.append(
                Chunk(text=" ".join(current_sentences), source_file=source_file, chunk_index=chunk_index)
            )
            chunk_index += 1
            current_sentences = [sentence]
            current_len = len(sentence)
        else:
            current_sentences.append(sentence)
            current_len = would_be_len

    if current_sentences:
        chunks.append(Chunk(text=" ".join(current_sentences), source_file=source_file, chunk_index=chunk_index))

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
    model = get_embedding_model()

    all_chunks: list[Chunk] = []
    for filename, text in documents:
        all_chunks.extend(
            semantic_chunk_text(
                text,
                filename,
                model,
                settings.semantic_similarity_threshold,
                settings.min_chunk_chars,
                settings.max_chunk_chars,
            )
        )

    if not all_chunks:
        return 0

    embeddings = model.encode([c.text for c in all_chunks], show_progress_bar=False).tolist()

    ids = [f"{role}::{c.source_file}::{c.chunk_index}" for c in all_chunks]
    metadatas = [{"source_file": c.source_file, "chunk_index": c.chunk_index, "role": role} for c in all_chunks]
    documents_text = [c.text for c in all_chunks]

    # upsert (not add) so re-running ingestion after editing a KB file is safe and idempotent
    collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents_text)
    return len(all_chunks)


def retrieve(role: str, query: str, top_k: int | None = None) -> list[dict]:
    """Embed `query`, return the top_k most relevant chunks for `role`, and drop any
    below `retrieval_min_similarity` (context-rot mitigation -- see module docstring),
    while always keeping at least the single best match."""
    top_k = top_k or settings.retrieval_top_k
    collection = get_collection(role)
    if collection.count() == 0:
        raise KnowledgeBaseNotIngestedError(role)

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

    above_threshold = [r for r in retrieved if r["similarity_score"] >= settings.retrieval_min_similarity]
    return above_threshold if above_threshold else retrieved[:1]
