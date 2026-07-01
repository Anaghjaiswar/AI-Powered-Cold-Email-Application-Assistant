from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from database import init_db
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize pgvector extension on startup
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Could not initialize database extension: {e}")
    yield

app = FastAPI(lifespan=lifespan)

# Mount static files (CSS, JS, assets)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "ok", "message": "Backend is running. Place index.html in the static folder."}

