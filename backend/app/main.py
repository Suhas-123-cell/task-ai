"""FastAPI application entry point: middleware, routers, startup, error handling."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db
from app.routers import candidates, interview, reports
from app.services.rag_pipeline import KnowledgeBaseNotIngestedError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized at %s", settings.database_url)
    yield


app = FastAPI(
    title=settings.app_name,
    description="RAG-driven, role-based candidate screening interview system.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(KnowledgeBaseNotIngestedError)
async def knowledge_base_not_ingested_handler(
    request: Request, exc: KnowledgeBaseNotIngestedError
) -> JSONResponse:
    # 503 (Service Unavailable), not 500: this is a known, actionable setup problem
    # (ingestion was never run for this role), not an unexpected server failure --
    # fails loudly with a fix-it message instead of silently falling back to
    # context-free question generation, which would be indistinguishable from a
    # working-but-low-relevance retrieval to anyone testing the app.
    logger.warning("Knowledge base not ingested for role '%s'", exc.role)
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


app.include_router(candidates.router)
app.include_router(interview.router)
app.include_router(reports.router)
