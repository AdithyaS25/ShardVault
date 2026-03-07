from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html

from app.core.database import engine, Base
from app.models import user  # ensure models are registered
from app.auth.routes import router as auth_router
from app.crypto.routes import router as crypto_router


# Disable default docs to customize Swagger
app = FastAPI(
    title="ShardLock Coordinator API",
    docs_url=None,
    redoc_url=None
)

# Include routers
app.include_router(auth_router)
app.include_router(crypto_router, prefix="/api/v1")

# CORS Configuration (Required for HttpOnly cookies)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000"],  # frontend URL
    allow_credentials=True,  # REQUIRED for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom Swagger UI with Dark Mode
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="ShardLock API Docs",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
            "theme": "dark"  # Enable dark mode
        },
    )


# Database startup
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def root():
    return {"message": "ShardLock Coordinator Running"}
