import os
from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import models
from schemas import GenerateEmailRequest, SendEmailRequest
from llm_engine import LLMEngine
from email_service import EmailService
from doc_processing_engine import shared_embeddings

class EmailController:
    """Controller handling business logic for generating email drafts and queueing emails for SMTP sending."""

    @staticmethod
    def generate_email_draft(db: Session, req: GenerateEmailRequest) -> dict:
        """
        Retrieves matching chunks across all completed resumes using pgvector,
        invokes the LLMEngine to generate the cold email draft, and parses the output.
        """
        # 1. Fetch user configuration settings
        settings = db.query(models.UserSettings).first()
        if not settings or not settings.groq_api_key:
            raise HTTPException(
                status_code=400,
                detail="Groq API key is not configured. Please save your Groq API key in Settings first."
            )

        # 2. Check if the user has uploaded any completed resumes
        completed_resume_exists = db.query(models.Resume).filter(models.Resume.status == "completed").first()
        if not completed_resume_exists:
            any_resume_exists = db.query(models.Resume).first()
            if any_resume_exists:
                raise HTTPException(
                    status_code=400,
                    detail="Your uploaded resumes are still being processed in the background. Please wait a few seconds and try again."
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No resumes found. Please upload at least one resume PDF before generating an email."
                )

        # 3. Embed the Job Description using the shared embeddings model
        try:
            query_vector = shared_embeddings.embed_query(req.job_description)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate query embedding: {str(e)}"
            )

        # 4. Query pgvector for the top 8 chunks matching the job description across all completed resumes
        chunks = (
            db.query(models.ResumeEmbedding)
            .join(models.Resume)
            .filter(models.Resume.status == "completed")
            .order_by(models.ResumeEmbedding.embedding.cosine_distance(query_vector))
            .limit(8)
            .all()
        )
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Could not retrieve matching skills context. Please ensure your resumes are uploaded successfully."
            )
        
        resume_text = "\n\n".join([chunk.content for chunk in chunks])

        # 4. Set up parameters and trigger generation
        footer_context = settings.email_footer or ""
        preferred_tone = settings.preferred_tone or "professional"
        email_length = settings.email_length or "medium"
        company_description = req.company_description or "A tech company"

        try:
            # Instantiate LLM Engine using the user's saved Groq key
            llm = LLMEngine(
                groq_api_key=settings.groq_api_key,
                temperature=0.5
            )
            raw_email = llm.generate_email_draft(
                resume_context=resume_text,
                footer_context=footer_context,
                job_description=req.job_description,
                company_description=company_description,
                preferred_tone=preferred_tone,
                email_length=email_length,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"LLM Generation failed: {str(e)}"
            )

        # 5. Parse output into Subject and Body based on strict prompt layout
        subject = ""
        body = ""
        raw_email_stripped = raw_email.strip()
        
        if raw_email_stripped.lower().startswith("subject:"):
            lines = raw_email_stripped.split("\n")
            # Extract subject (remove 'Subject:' text)
            subject = lines[0][len("subject:"):].strip()
            # Extract email body
            body = "\n".join(lines[1:]).strip()
        else:
            # Fallback in case layout instructions were bypassed
            subject = "Outreach regarding open position"
            body = raw_email_stripped

        return {
            "subject": subject,
            "body": body
        }

    @staticmethod
    def send_outbound_email(db: Session, req: SendEmailRequest, background_tasks: BackgroundTasks) -> dict:
        """
        Queues the email for SMTP transmission in a background task to prevent blocking the HTTP response.
        """
        # Quick validation of credentials before queueing
        settings = db.query(models.UserSettings).first()
        if not settings or not settings.sender_email or not settings.sender_app_password:
            raise HTTPException(
                status_code=400,
                detail="Sender credentials (email & app password) are not configured in Settings."
            )

        # Queue the email sending utility in the background
        background_tasks.add_task(
            EmailService.send_email_with_resume,
            db,
            req.recipient_email,
            req.subject,
            req.body,
            req.resume_id
        )

        return {
            "status": "success",
            "message": "Email sending has been queued in the background."
        }
