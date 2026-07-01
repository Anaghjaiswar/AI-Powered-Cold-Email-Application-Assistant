# import typing
# import numpy
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from database import init_db
from routes import router as api_router
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run database initialization on startup
    try:
        init_db()
        # Clean up any resumes stuck in "processing" state from an interrupted previous session
        from database import SessionLocal
        import models
        db = SessionLocal()
        try:
            stuck_resumes = db.query(models.Resume).filter(models.Resume.status == "processing").all()
            if stuck_resumes:
                print(f"Cleaning up {len(stuck_resumes)} resumes stuck in processing state...")
                for r in stuck_resumes:
                    r.status = "failed"
                    r.error_message = "Ingestion interrupted by server restart."
                db.commit()
        except Exception as db_err:
            print(f"Warning: Could not clean up stuck processing states: {db_err}")
        finally:
            db.close()
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
    yield

app = FastAPI(lifespan=lifespan)

# Register global API router
app.include_router(api_router)

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

