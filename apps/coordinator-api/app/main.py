"""
main.py — DIFF from vault-management version
=============================================
ONE change only:

ADDED: audit router import and registration

--- existing router block ---
from app.vault.routes import router as vault_router

app.include_router(auth_router)
app.include_router(crypto_router, prefix="/api/v1")
app.include_router(shamir_router, prefix="/api/v1")
app.include_router(vault_router,  prefix="/api/v1")

+++ replace with +++
from app.vault.routes import router as vault_router
from app.audit.routes import router as audit_router      # NEW

app.include_router(auth_router)
app.include_router(crypto_router, prefix="/api/v1")
app.include_router(shamir_router, prefix="/api/v1")
app.include_router(vault_router,  prefix="/api/v1")
app.include_router(audit_router,  prefix="/api/v1")      # NEW
"""

# ── FULL updated main.py for reference ───────────────────────────────────────

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html

from app.core.database import engine, Base
from app.models import user, vault_entry
from app.auth.routes import router as auth_router
from app.crypto.routes import router as crypto_router
from app.shamir.routes import router as shamir_router
from app.vault.routes import router as vault_router
from app.audit.routes import router as audit_router          # NEW


app = FastAPI(
    title="ShardLock Coordinator API",
    docs_url=None,
    redoc_url=None
)

app.include_router(auth_router)
app.include_router(crypto_router, prefix="/api/v1")
app.include_router(shamir_router, prefix="/api/v1")
app.include_router(vault_router,  prefix="/api/v1")
app.include_router(audit_router,  prefix="/api/v1")          # NEW

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="ShardLock API Docs",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
            "theme": "dark"
        },
    )


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def root():
    return {"message": "ShardLock Coordinator Running"}
