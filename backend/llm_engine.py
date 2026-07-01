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
                "You are an expert cold email outbound copywriter. Your job is to construct a highly personalized, "
                "impactful job application email based on the candidate's resume, footer configuration, user preferences, "
                "and job/company details.\n\n"
                "INFORMATION PRIORITIZATION HIERARCHY (Strictly prioritize information in this order):\n"
                "1. HIGHEST PRIORITY - Job & Resume Match: Extract actual skills, accomplishments, and experience from the Candidate Resume Context that directly match the role requirements in the Job Description. Do not fabricate or invent any experience or skills.\n"
                "2. SECOND PRIORITY - Company Details: Incorporate relevant context from the company's product domain, culture, or mission to show genuine interest and alignment.\n"
                "3. THIRD PRIORITY - User Preferences: Fit the output into the user's preferred tone and length constraints. These are style constraints, but must never overshadow the core job-resume alignment.\n\n"
                "STRICT LAYOUT & STYLE REQUIREMENTS:\n"
                "1. Output MUST start with 'Subject: [Compelling, short subject line]'. Do not include any greeting or preamble before it.\n"
                "2. Leave exactly one empty line between the Subject line and the email body.\n"
                "3. Apply selective rich text formatting (such as **bold** or *italic* tags) or bullet points when necessary to cleanly emphasize key metrics, achievements, or matching technology stacks.\n"
                "4. Append the provided dynamic footer exactly at the bottom of the email.\n"
                "5. Keep the tone humble, confident, value-driven, and alignment-focused, tailored specifically to the user's preferred tone: {preferred_tone}.\n"
                "6. Write the email to match the user's preferred email length: {email_length}.\n"
                "7. Do NOT leave any bracketed placeholders (like [Your Name] or [Recipient's Name]) in the final email output. Write naturally if details are missing.\n\n"
                "USER PREFERENCES:\n"
                "- Preferred Tone: {preferred_tone}\n"
                "- Preferred Length: {email_length}\n\n"
                "CANDIDATE RESUME CONTEXT:\n{resume_context}\n\n"
                "EMAIL FOOTER CONFIG:\n{footer_context}\n\n"
                "JOB DESCRIPTION:\n{job_description}\n"
                "COMPANY DETAILS:\n{company_description}"
            )),
            ("human", "Generate the draft tailored for target recipient: {recipient_email}")
        ])

        self.prompt = prompt or self.system_prompt

        self.CHAIN = self.prompt | self.llm | StrOutputParser()


    def generate_email_draft(
        self,
        resume_context: str,
        footer_context: str,
        job_description: str,
        company_description: str,
        preferred_tone: str,
        email_length: str,
        recipient_email: str,
    ) -> str:
        """Generates a cold email draft based on resume, footer, preferences, and job/company details."""
        try:
            return self.CHAIN.invoke({
                "resume_context": resume_context,
                "footer_context": footer_context,
                "job_description": job_description,
                "company_description": company_description,
                "preferred_tone": preferred_tone,
                "email_length": email_length,
                "recipient_email": recipient_email
            })
        except Exception as e:
            raise RuntimeError(f"Error generating email draft: {e}") from e
