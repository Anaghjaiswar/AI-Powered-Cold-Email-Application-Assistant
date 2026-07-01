from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from database import Base

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    embeddings = relationship("ResumeEmbedding", back_populates="resume", cascade="all, delete-orphan")

class ResumeEmbedding(Base):
    __tablename__ = "resume_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    
    embedding = Column(Vector(384), nullable=True)
    
    resume = relationship("Resume", back_populates="embeddings")

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    groq_api_key = Column(String(255), nullable=True)
    sender_email = Column(String(255), nullable=True)
    sender_app_password = Column(String(255), nullable=True)
    email_footer = Column(Text, nullable=True) 
    preferred_tone = Column(String(50), nullable=True)  # Limited options: e.g., professional, conversational, creative, short
    email_length = Column(String(50), nullable=True)    # Limited options: e.g., short, medium, long
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

