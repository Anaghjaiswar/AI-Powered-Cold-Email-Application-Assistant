import os
from typing import Optional
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chat_models import init_chat_model

load_dotenv()

class LLMEngine:
    """Core LLM reasoning engine for generating tailored cold emails.

    Uses Groq to draft highly targeted outreach emails based on the 
    candidate's resume, footer configuration, user preferences, and job/company details.
    """

    def __init__(
        self,
        groq_api_key: str,
        model_name: str = "llama-3.3-70b-versatile",
        model_provider: str = "groq",
        temperature: float = 0.6,
        prompt: Optional[ChatPromptTemplate] = None,
    ) -> None:
        """Initializes the LLMEngine with the Chat model and prompt configurations."""
        if not groq_api_key:
            raise ValueError("groq_api_key must be provided and cannot be empty.")

        os.environ["GROQ_API_KEY"] = groq_api_key

        # Initialize the chat model
        self.llm = init_chat_model(
            model_name,
            model_provider=model_provider,
            temperature=temperature,
            api_key=groq_api_key,
        )

     
        self.system_prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert cold email writer. Your job is to draft a highly personalized, "
                "compelling cold email for a job application based on the candidate's resume, footer, and job details.\n\n"
                "STYLE & COLD OUTREACH INSTRUCTIONS:\n"
                "1. Hook with the Soham Parekh style: Start directly with a love for what the company/product is doing. Immediately follow with a short, raw vulnerability hook reflecting a singular focus on building (e.g., 'I don’t have many hobbies outside coding. I am not athletic, bad at singing, don’t drink, can’t dance. Building is the only thing I am good at. At this point, I want to be a part of taking something from 0 -> 1 or 1 -> 100. I just want to be heads down chasing that goal.').\n"
                "2. The Builder Persona: Position yourself as an early-team developer who wants to execute. Avoid pompous self-titles like 'seasoned developer' or 'expert' for intern/junior roles.\n"
                "3. Highlight specific metrics: Extract real accomplishments, percentages, and metrics from the candidate's resume context (e.g., '69% of commits, 67K LOC', 'concurrency-safety using Redis and Lua', 'Go/Gin microservice with 96% commits') to back up your technical capabilities.\n"
                "4. Show, don't parrot: Never replicate the job description responsibilities as a list. Show how your specific projects maps to their needs.\n"
                "5. Keep the tone {preferred_tone} and humble yet confident.\n"
                "6. Write the email to match the preferred length: {email_length}.\n\n"
                "STRICT LAYOUT REQUIREMENTS:\n"
                "1. Output MUST start with 'Subject: [Short, compelling subject line]'. Do not write any preamble before it.\n"
                "2. Leave exactly one empty line between the Subject line and the email body.\n"
                "3. Append the provided dynamic footer exactly at the bottom of the email.\n"
                "4. Do NOT leave any bracketed placeholders in the output. Use the candidate's actual details.\n\n"
                "CANDIDATE RESUME:\n{resume_context}\n\n"
                "EMAIL FOOTER:\n{footer_context}\n\n"
                "JOB DESCRIPTION:\n{job_description}\n"
                "COMPANY CONTEXT:\n{company_description}"
            )),
            ("human", "Generate the cold email draft tailored for this job application based on the provided details.")
        ])

        self.prompt = prompt or self.system_prompt

        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate_email_draft(
        self,
        resume_context: str,
        footer_context: str,
        job_description: str,
        company_description: str,
        preferred_tone: str,
        email_length: str,
    ) -> str:
        """Generates a cold email draft based on resume, footer, preferences, and job/company details."""
        try:
            return self.chain.invoke({
                "resume_context": resume_context,
                "footer_context": footer_context,
                "job_description": job_description,
                "company_description": company_description,
                "preferred_tone": preferred_tone,
                "email_length": email_length,
            })
        except Exception as e:
            raise RuntimeError(f"Error generating email draft: {e}") from e
