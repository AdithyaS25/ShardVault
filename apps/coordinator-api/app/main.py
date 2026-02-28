from fastapi import FastAPI
from app.core.database import engine, Base
from app.models import user

app = FastAPI(title="ShardLock Coordinator API")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
def root():
    return {"message": "ShardLock Coordinator Running"}
