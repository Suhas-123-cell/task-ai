"""
Centralized application configuration.

All tunables are sourced from environment variables (with sane local-dev
defaults) so the same codebase can move between local, CI, and deployed
environments without code changes -- per the assignment's requirement that
configuration be handled through environment variables.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_ROOT / "data"
KNOWLEDGE_BASE_DIR = BACKEND_ROOT / "knowledge_base"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Service metadata ---
    app_name: str = "AI Candidate Screening System"
    environment: str = "development"

    # --- Persistence ---
    database_url: str = f"sqlite:///{DATA_DIR / 'app.db'}"
    chroma_persist_dir: str = str(DATA_DIR / "chroma")
    upload_dir: str = str(DATA_DIR / "uploads")

    # --- RAG / embeddings ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Semantic chunking: split at sentence boundaries where embedding similarity to
    # the next sentence drops below this threshold (a topic shift), instead of a
    # fixed character count. min/max bound the result so a long run of similar
    # sentences doesn't produce one giant chunk, and a run of dissimilar short
    # sentences doesn't produce many tiny, context-poor ones.
    semantic_similarity_threshold: float = 0.55
    min_chunk_chars: int = 300
    max_chunk_chars: int = 1400
    retrieval_top_k: int = 4
    # Context-rot mitigation: a retrieved chunk below this cosine similarity adds
    # noise/dilution to the LLM prompt rather than useful grounding, so it's dropped
    # even if that means returning fewer than retrieval_top_k chunks. Always keeps at
    # least one chunk (the single best match) so a question is never generated with
    # zero context.
    retrieval_min_similarity: float = 0.15

    # --- LLM (Groq) ---
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.6
    llm_max_tokens: int = 700

    # --- Interview lifecycle ---
    max_interview_questions: int = 5

    # --- CORS ---
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
