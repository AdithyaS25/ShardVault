from fastapi import FastAPI
from app.core.database import engine, Base
from app.models import user
from app.auth.routes import router as auth_router

app = FastAPI(title="ShardLock Coordinator API")

app.include_router(auth_router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
def root():
    return {"message": "ShardLock Coordinator Running"}
