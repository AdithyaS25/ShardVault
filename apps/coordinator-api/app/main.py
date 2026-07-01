from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from app.core.config import settings
from app.core.database import engine, Base
from app.models import user, vault_entry
from app.auth.routes import router as auth_router
from app.crypto.routes import router as crypto_router
from app.shamir.routes import router as shamir_router
from app.vault.routes import router as vault_router
from app.audit.routes import router as audit_router
from app.admin.routes import router as admin_router
from app.core.database import engine, Base, AsyncSessionLocal


app = FastAPI(
    title="ShardLock Coordinator API",
    docs_url=None,
    redoc_url=None
)

app.include_router(auth_router)
app.include_router(crypto_router, prefix="/api/v1")
app.include_router(shamir_router, prefix="/api/v1")
app.include_router(vault_router,  prefix="/api/v1")
app.include_router(audit_router,  prefix="/api/v1")
app.include_router(admin_router,  prefix="/api/v1")

allowed_origins = [
    origin.strip()
    for origin in settings.ALLOWED_ORIGINS.split(",")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
    # Tables are managed via migrations on Supabase — no create_all needed.
    # Just verify the connection is reachable.
    from sqlalchemy import text
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))


@app.get("/")
async def root():
    return {"message": "ShardLock Coordinator Running"}