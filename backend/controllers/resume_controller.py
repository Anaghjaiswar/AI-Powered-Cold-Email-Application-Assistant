import os
import uuid
from fastapi import UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import models
from doc_processing_engine import get_doc_processor
from database import SessionLocal


ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

def process_resume_in_background(resume_id: int, filepath: str):
    """Background task to extract text from a resume PDF, split it into chunks, and store pgvector embeddings."""
    db = SessionLocal()
    try:
        # Run Document Processing Engine to convert, chunk, and embed via pgvector
        get_doc_processor().process_pdf(db, resume_id, filepath)
        
        # On success, update status to completed
        resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
        if resume:
            resume.status = "completed"
            db.commit()
    except Exception as e:
        # On failure, update status to failed and log the error message
        db.rollback()
        resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
        if resume:
            resume.status = "failed"
            resume.error_message = str(e)
            db.commit()
    finally:
        db.close()

class ResumeController:
    """Class-based controller handling business logic and DB CRUD operations for resumes."""

    @staticmethod
    def list_resumes(db: Session):
        return db.query(models.Resume).all()

    @staticmethod
    def get_resume(db: Session, resume_id: int):
        resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
        if not resume:
            raise HTTPException(status_code=404, detail=f"Resume with ID {resume_id} not found.")
        return resume

    @staticmethod
    def create_resume(db: Session, file: UploadFile, background_tasks: BackgroundTasks):
        # Check file extension
        file_ext = os.path.splitext(file.filename)[1]
        if file_ext.lower() != ".pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")


        os.makedirs(ASSETS_DIR, exist_ok=True)

        # Generate unique file name to prevent collision
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(ASSETS_DIR, unique_filename)

        # Write PDF to assets folder
        try:
            with open(filepath, "wb") as buffer:
                while content := file.file.read(1024 * 1024):
                    buffer.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save PDF on disk: {str(e)}")

        # Save record to postgres as "processing"
        resume = models.Resume(filename=file.filename, filepath=filepath, status="processing")
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # Queue the PDF extraction and vector embedding generation in the background
        background_tasks.add_task(process_resume_in_background, resume.id, filepath)

        return resume

    @staticmethod
    def delete_resume(db: Session, resume_id: int):
        resume = ResumeController.get_resume(db, resume_id)

        # Delete local file from disk
        if os.path.exists(resume.filepath):
            try:
                os.remove(resume.filepath)
            except Exception as e:
                print(f"Warning: Failed to delete local physical file {resume.filepath}: {e}")

        db.delete(resume)
        db.commit()
        return resume
