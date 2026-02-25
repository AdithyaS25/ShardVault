from fastapi import FastAPI

app = FastAPI(title="ShardLock Coordinator API")

@app.get("/")
def root():
    return {"message": "ShardLock Coordinator Running"}

