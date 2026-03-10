"""
main.py — ShardLock Share Node Service
=======================================
Independent microservice responsible for storing and retrieving
a single encrypted secret fragment (share) per vault entry.

Per §2.12 monorepo structure — lives at services/share-node/
Per §2.11 deployment — deployed independently on Render or Fly.io

Security model:
  - Accepts ONLY internal service token authentication (§2.4)
  - Never receives master passwords or plaintext secrets
  - Stores only one share per vault_entry_id — never the full secret
  - A single compromised node reveals nothing without K-1 other shares

Each deployed instance is one share node.
N=4 nodes are deployed, each holding 1 of the 4 shares.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.routes.shares import router as shares_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="ShardLock Share Node",
    description=(
        "Internal microservice for storing encrypted secret fragments. "
        "All endpoints require internal service token authentication. "
        "Not exposed to end users."
    ),
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,   # Hide docs in production
    redoc_url=None,
    lifespan=lifespan,
)

# CORS — only coordinator should reach this service
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Internal routes only — no /api/v1/auth, no public endpoints
app.include_router(shares_router, prefix="/internal")


@app.get("/health", tags=["Health"])
async def health():
    """Public health check — used by deployment platform (Render/Fly.io)."""
    return {
        "status"   : "ok",
        "service"  : "share-node",
        "node_id"  : settings.NODE_ID,
    }