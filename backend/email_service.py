import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional
from sqlalchemy.orm import Session
import models

class EmailService:
    """Service layer handling email compilation, attachment generation, and dispatch via SMTP."""

    @staticmethod
    def send_email_with_resume(
        db: Session,
        recipient_email: str,
        subject: str,
        body: str,
        resume_id: Optional[int] = None
    ) -> bool:
        """
        Sends an email with SMTP SSL, optionally attaching the selected resume PDF file.
        Uses credentials stored in the UserSettings database table.
        """
        # 1. Fetch sender credentials from user settings
        settings = db.query(models.UserSettings).first()
        if not settings or not settings.sender_email or not settings.sender_app_password:
            raise ValueError("Sender email and app password must be configured in user settings before sending.")

        sender_email = settings.sender_email
        sender_password = settings.sender_app_password

        # 2. Build the multi-part email structure
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject

        # Attach email body text
        msg.attach(MIMEText(body, "plain"))

        # 3. Read and attach PDF file if resume_id is provided
        if resume_id is not None:
            resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
            if not resume:
                raise ValueError(f"Resume with ID {resume_id} not found in database.")
            
            if not os.path.exists(resume.filepath):
                raise FileNotFoundError(f"PDF file not found on disk at: {resume.filepath}")

            try:
                with open(resume.filepath, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    # Use original user-facing filename for the email attachment name
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={resume.filename}"
                    )
                    msg.attach(part)
            except Exception as e:
                raise RuntimeError(f"Failed to read or attach resume PDF: {str(e)}")

        # 4. Connect to Gmail SMTP server using SSL on port 465
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
            return True
        except smtplib.SMTPAuthenticationError:
            raise ValueError("SMTP Authentication failed. Please check that your sender email and app password are correct.")
        except Exception as e:
            raise RuntimeError(f"SMTP dispatch failure: {str(e)}")
