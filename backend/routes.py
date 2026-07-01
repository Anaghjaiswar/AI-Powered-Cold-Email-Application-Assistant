from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from schemas import UserSettingsSchema, ResumeSchema, GenerateEmailRequest, GenerateEmailResponse, SendEmailRequest
from controllers.settings_controller import UserSettingsController
from controllers.resume_controller import ResumeController
from controllers.email_controller import EmailController
from typing import List

router = APIRouter()

# --- USER SETTINGS ENDPOINTS ---

@router.get("/api/settings", response_model=UserSettingsSchema, tags=["settings"])
def get_user_settings(db: Session = Depends(get_db)):
    return UserSettingsController.get_settings(db)

@router.put("/api/settings", response_model=UserSettingsSchema, tags=["settings"])
def update_user_settings(settings: UserSettingsSchema, db: Session = Depends(get_db)):
    return UserSettingsController.update_settings(db, settings)

@router.delete("/api/settings", response_model=UserSettingsSchema, tags=["settings"])
def clear_user_settings(db: Session = Depends(get_db)):
    return UserSettingsController.clear_settings(db)


# --- RESUME ENDPOINTS ---

@router.get("/api/resumes", response_model=List[ResumeSchema], tags=["resumes"])
def list_resumes(db: Session = Depends(get_db)):
    return ResumeController.list_resumes(db)

@router.get("/api/resumes/{resume_id}", response_model=ResumeSchema, tags=["resumes"])
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    return ResumeController.get_resume(db, resume_id)

@router.post("/api/resumes", response_model=ResumeSchema, status_code=201, tags=["resumes"])
def upload_resume(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    return ResumeController.create_resume(db, file, background_tasks)

@router.delete("/api/resumes/{resume_id}", response_model=ResumeSchema, tags=["resumes"])
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    return ResumeController.delete_resume(db, resume_id)


# --- EMAIL DRAFTING & SENDING ENDPOINTS ---

@router.post("/api/generate", response_model=GenerateEmailResponse, tags=["emails"])
def generate_email_draft(req: GenerateEmailRequest, db: Session = Depends(get_db)):
    return EmailController.generate_email_draft(db, req)

@router.post("/api/send-email", tags=["emails"])
def send_email(req: SendEmailRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return EmailController.send_outbound_email(db, req, background_tasks)

