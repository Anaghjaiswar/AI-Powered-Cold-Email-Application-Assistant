from pydantic import BaseModel
from typing import Optional

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
