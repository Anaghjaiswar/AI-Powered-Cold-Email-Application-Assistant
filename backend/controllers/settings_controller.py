from sqlalchemy.orm import Session
import models
from schemas import UserSettingsSchema

class UserSettingsController:
    """Controller containing the business logic and database CRUD operations for User Settings."""

    @staticmethod
    def get_settings(db: Session) -> models.UserSettings:
        """Retrieves the current settings row from the database. Creates it if missing."""
        settings = db.query(models.UserSettings).first()
        if not settings:
            settings = models.UserSettings(
                preferred_tone="professional",
                email_length="medium"
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    @staticmethod
    def update_settings(db: Session, data: UserSettingsSchema) -> models.UserSettings:
        """Updates the current settings row with the provided values."""
        settings = UserSettingsController.get_settings(db)
        
        # Loop through Pydantic fields and set them on the SQLAlchemy model
        for field, value in data.dict(exclude_unset=True).items():
            setattr(settings, field, value)
            
        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    def clear_settings(db: Session) -> models.UserSettings:
        """Resets the settings fields back to standard defaults."""
        settings = UserSettingsController.get_settings(db)
        settings.groq_api_key = None
        settings.sender_email = None
        settings.sender_app_password = None
        settings.email_footer = None
        settings.preferred_tone = "professional"
        settings.email_length = "medium"
        
        db.commit()
        db.refresh(settings)
        return settings
