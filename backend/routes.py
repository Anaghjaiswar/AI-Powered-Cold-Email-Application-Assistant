from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import UserSettingsSchema
from controllers.settings_controller import UserSettingsController

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
