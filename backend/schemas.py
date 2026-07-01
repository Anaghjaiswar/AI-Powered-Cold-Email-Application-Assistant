from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserSettingsSchema(BaseModel):
    groq_api_key: Optional[str] = None
    sender_email: Optional[str] = None
    sender_app_password: Optional[str] = None
    email_footer: Optional[str] = None
    preferred_tone: Optional[str] = None
    email_length: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "groq_api_key": "gsk_...",
                "sender_email": "user@example.com",
                "sender_app_password": "abcd efgh ijkl mnop",
                "email_footer": "Best regards,\nJohn Doe",
                "preferred_tone": "professional",
                "email_length": "medium"
            }
        }

class ResumeSchema(BaseModel):
    id: int
    filename: str
    filepath: str
    status: str
    error_message: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "filename": "my_resume.pdf",
                "filepath": "/app/assets/1234-5678-my_resume.pdf",
                "status": "processing",
                "error_message": None,
                "uploaded_at": "2026-07-01T08:00:00Z"
            }
        }

class GenerateEmailRequest(BaseModel):
    company_description: Optional[str] = ""
    job_description: str

class GenerateEmailResponse(BaseModel):
    subject: str
    body: str

class SendEmailRequest(BaseModel):
    recipient_email: str
    subject: str
    body: str
    resume_id: Optional[int] = None


