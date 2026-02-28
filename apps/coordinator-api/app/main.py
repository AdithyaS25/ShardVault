from fastapi import FastAPI
from app.core.database import engine, Base
from app.models import user
from app.auth.routes import router as auth_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ShardLock Coordinator API")

app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000"],  # frontend later
    allow_credentials=True,  # IMPORTANT
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
def root():
    return {"message": "ShardLock Coordinator Running"}
