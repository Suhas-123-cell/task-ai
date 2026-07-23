"""FastAPI application entry point: middleware, routers, startup, error handling."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import BACKEND_ROOT, get_settings
from app.database import init_db
from app.routers import candidates, interview, reports
from app.services.rag_pipeline import KnowledgeBaseNotIngestedError

# Present only in the combined single-service Docker deploy (see repo-root
# Dockerfile): the frontend's `npm run build` output gets copied here so this
# one FastAPI process can serve both the API and the built React app from a
# single origin, avoiding CORS setup and a second Railway service entirely.
# Absent in local dev (frontend runs on its own Vite dev server instead).
FRONTEND_DIST_DIR = BACKEND_ROOT / "static"

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


if FRONTEND_DIST_DIR.is_dir():
    # Registered AFTER the API routers above: FastAPI/Starlette matches routes
    # in registration order, so /api/* is resolved by the routers first and
    # never shadowed by the routes below.
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST_DIR / "assets"), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str) -> FileResponse:
        # Single-page app fallback: this app doesn't use client-side routing
        # (no react-router, just in-memory state -- see frontend/src/App.jsx),
        # so in practice this only ever serves "/", but a catch-all fallback
        # to index.html is the standard, safe pattern regardless.
        return FileResponse(FRONTEND_DIST_DIR / "index.html")
