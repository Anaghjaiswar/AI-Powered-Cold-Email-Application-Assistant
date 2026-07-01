# ColdMail AI - Personalized Outbound Assistant

ColdMail AI is a modern, self-hosted web application that automates the generation of highly personalized, context-aware job application cold emails. Powered by layout-aware RAG (Retrieval-Augmented Generation), it parses multiple candidate resumes (e.g. AI stack, Backend stack, Fullstack), performs semantic search matching role requirements, and drafts outbound emails using Groq (Llama 3.3 70B) styled to the user's preferences. It also includes a background SMTP mailer for immediate dispatch with resume attachments.

---

## 🚀 Getting Started

Setting up the entire suite of services is fully automated using Docker.

### Prerequisites
* Docker installed on your host system.
* Docker Compose installed.

### Run via Docker Compose
Clone the repository and run the following command in the root folder:

```bash
# Spin up both PostgreSQL (pgvector) and FastAPI container services
docker-compose up -d --build
```

The application will be accessible at:
* **Frontend Web UI**: [http://localhost:8000](http://localhost:8000)
* **API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🛠️ Tech Stack Used

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.11) | High-performance, asynchronous REST API layer. |
| **Database** | PostgreSQL + pgvector | Relational data persistence with native vector similarity search. |
| **Document Processing** | Docling (by IBM) | Layout-aware document converter translating PDFs to structured Markdown. |
| **Embeddings Model** | Hugging Face (`all-MiniLM-L6-v2`) | Local execution of semantic text embedding generation (384-dim). |
| **LLM Orchestration** | LangChain & langchain-groq | Prompt templates and tool-calling execution. |
| **inference API** | Groq (Llama 3.3 70B Versatile) | Low-latency drafting engine using context-rich prompting. |
| **Email Parsing** | Marko | Parses markdown generated drafts into styled HTML MIME blocks. |
| **SMTP Delivery** | Python `smtplib` + SSL | Secure outbound transmission (port 465) with PDF attachment encoding. |
| **Frontend** | HTML5, CSS3, JavaScript | Lightweight SPA with typewriter stream simulation and markdown previews. |

---

## 📐 System Architecture

The following diagram illustrates how the frontend client, FastAPI backend, pgvector database, and external APIs communicate:

```mermaid
graph TD
    User[User Browser - Client UI]
    FastAPI[FastAPI Backend Server]
    DB[(PostgreSQL + pgvector)]
    Groq[Groq API - Llama 3.3]
    SMTP[Gmail SMTP SSL Server]
    
    User -->|1. Settings & PDF Resumes| FastAPI
    User -->|3. Generate Email Request| FastAPI
    User -->|4. Send SMTP Request| FastAPI
    
    FastAPI -->|Store Settings & Metadata| DB
    FastAPI -->|Insert Vector Embeddings| DB
    FastAPI -->|2. Query Cosine Distance| DB
    FastAPI -->|Query context matches| DB
    FastAPI -->|Invoke Generation Chain| Groq
    FastAPI -->|Background SMTP SSL| SMTP
```

---

## 🔄 Pipeline Sequence Flowchart

The workflow of ingestion, indexing, retrieval, generation, and dispatch:

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Frontend)
    participant API as FastAPI Backend
    participant Doc as Docling Engine
    participant DB as pgvector DB
    participant LLM as Groq LLM (Llama 3)
    participant SMTP as SMTP Mailer
    
    %% Upload Phase
    Note over User, DB: 1. Ingestion & RAG Indexing Pipeline
    User->>API: Upload PDF Resume
    API-->>User: HTTP 201 (Status: Processing)
    Note right of API: Background Task Triggered
    API->>Doc: Convert PDF to Layout-aware Markdown
    Doc-->>API: Structured Markdown Text
    API->>API: Chunk Text (Headers + Safety Splitter)
    API->>API: Generate Embeddings (all-MiniLM-L6-v2)
    API->>DB: Persist text chunks and 384-dim embeddings
    API->>DB: Update Resume Status ("completed")
    User->>API: Poll Resume Status
    API-->>User: Return Status (Status badge switches to "Index Ready")
    
    %% Generation Phase
    Note over User, LLM: 2. Email Generation & Retrieval Pipeline
    User->>API: Click Generate (Job Description + Company Details)
    API->>API: Embed Job Description Text
    API->>DB: Query Top 8 matching chunks (Cosine Distance)
    DB-->>API: Returns relevant candidate skills context
    API->>LLM: Tailored prompt (Resume context + Job + Footer preferences)
    LLM-->>API: Subject & Body Draft
    API-->>User: Return generated draft
    User->>User: View text & type stream / double-click to edit Markdown
    
    %% Send Phase
    Note over User, SMTP: 3. Secure Outbound SMTP Pipeline
    User->>API: Input recipient email & click Send
    API-->>User: HTTP 200 (Outbound queued in background)
    Note right of API: Background Task Triggered
    API->>SMTP: Connect SMTP SSL (Port 465) & login
    API->>SMTP: Dispatch MIME Email (Styled HTML + PDF Attachment)
    SMTP-->>API: Outbound delivered successfully
```

---

## 📂 Project Structure

```
AI-Powered-Cold-Email-Application-Assistant/
├── backend/
│   ├── assets/                 # Storage for physically uploaded PDFs
│   ├── controllers/            # Class-based business logic controllers
│   │   ├── email_controller.py # SMTP SSL queues & pgvector RAG logic
│   │   ├── resume_controller.py# PDF uploading & background processing triggers
│   │   └── settings_controller.py # Outbound profile settings CRUD
│   ├── database.py             # SQLAlchemy configuration, migrations & startup hooks
│   ├── doc_processing_engine.py# Docling PDF parsing & pgvector indexing
│   ├── Dockerfile              # Backend container build configuration
│   ├── email_service.py        # SMTP SSL dispatch and HTML MIME compilation
│   ├── llm_engine.py           # LangChain Groq prompt orchestration
│   ├── main.py                 # FastAPI application entrypoint & static mount
│   ├── models.py               # SQLAlchemy database models (Settings, Resumes, Chunks)
│   ├── requirements.txt        # Python dependency declarations
│   ├── routes.py               # Unified REST API endpoint routing
│   └── schemas.py              # Pydantic validation schemas
├── frontend/                   # Dashboard static files
│   ├── index.html              # Welcome screen, credentials form, and split-pane workspace
│   ├── script.js               # State manager, file drop listeners, and typewriter streams
│   └── style.css               # Variable-theme layout stylesheet (dark & light modes)
├── docker-compose.yml          # Container coordination configuration
└── readme.md                   # System documentation (this file)
```

---

## 📄 Module Descriptions

| Module | Purpose | Key Responsibilities |
| :--- | :--- | :--- |
| **`main.py`** | Entrypoint | Initializes FastAPI, triggers database migrations, mounts `/static` endpoints, and clears stuck processing tasks on reboot. |
| **`routes.py`** | Routing | Maps API endpoints (`/api/settings`, `/api/resumes`, `/api/generate`, `/api/send-email`) to their respective controller classes. |
| **`schemas.py`** | Validation | Defines Pydantic data schemas validating API payloads and database serialization limits. |
| **`models.py`** | Database Models | Outlines SQL tables for User Settings, Resume metadata, and pgvector Resume Embeddings (384 dimensions). |
| **`controllers/`** | Business Logic | Isolates endpoint interactions (Settings storage, Resume CRUD pipelines, and Outbound execution). |
| **`doc_processing_engine.py`** | Document Ingestion | Deferred loading of `Docling` to extract layout-aware markdown and `langchain` to generate vector embeddings. |
| **`llm_engine.py`** | RAG Generation | Invokes Llama 3.3 via Groq using matching resume chunks as context to write tailored cold emails. |
| **`email_service.py`** | SMTP Delivery | Preprocesses Markdown into left-aligned HTML paragraphs and dispatches emails with attachment encodings. |
| **`frontend/`** | Web Client UI | A 4-step responsive dashboard walkthrough (Welcome $\rightarrow$ Credentials setup $\rightarrow$ Resume Upload Drawer $\rightarrow$ Workspace Workspace). |
