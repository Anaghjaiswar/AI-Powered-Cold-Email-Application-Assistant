import os
from typing import List, Tuple, Optional
from docling.document_converter import DocumentConverter
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings



class DocProcessingEngine:
    """Document processing engine for RAG (Retrieval-Augmented Generation) applications.

    This engine orchestrates the document ingestion pipeline. It converts raw PDFs into
    layout-aware Markdown text, splits the content using semantic headers to maintain
    contextual boundaries, performs secondary character-based chunking for safety, and
    saves the generated embeddings into a PostgreSQL database using pgvector.
    """

    def __init__(
        self,
        embeddings: Optional[HuggingFaceEmbeddings] = None,
    ) -> None:
        """Initializes the DocProcessingEngine with conversion, splitting, and embedding configurations."""
        self.converter: DocumentConverter = DocumentConverter()
        
        self.headers_to_split_on: List[Tuple[str, str]] = [
            ("#", "Header_1"),
            ("##", "Header_2"),
            ("###", "Header_3")
        ]
        
        self.markdown_splitter: MarkdownHeaderTextSplitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on
        )
        
        self.safety_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=60,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.embeddings: HuggingFaceEmbeddings = embeddings or HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    def convert_to_markdown(self, pdf_path: str) -> str:
        """Converts a PDF document to a structured Markdown format."""
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"PDF file not found: '{pdf_path}'")
        
        try:
            conversion_result = self.converter.convert(pdf_path)
            markdown_text = conversion_result.document.export_to_markdown()
            return markdown_text
        except Exception as e:
            raise RuntimeError(f"Error converting PDF to Markdown for '{pdf_path}': {e}") from e

    def get_structured_docs(self, markdown_text: str) -> List[Document]:
        """Splits Markdown text into semantically cohesive document chunks.

        This method first divides the text based on markdown headers (e.g., # H1, ## H2),
        preserving hierarchical document structure. It then applies a secondary recursive
        character splitter to ensure that each chunk does not exceed token or length safety limits.
        """
        structured_docs = self.markdown_splitter.split_text(markdown_text)
        final_chunks = self.safety_splitter.split_documents(structured_docs)
        return final_chunks

    def save_to_postgres(self, db_session, resume_id: int, final_chunks: List[Document]) -> None:
        """Generates vector embeddings for document chunks and persists them to PostgreSQL pgvector."""
        from models import ResumeEmbedding
        
        # Extract the text content from chunks
        texts = [chunk.page_content for chunk in final_chunks]
        
        # Generate embeddings in batch
        embeddings = self.embeddings.embed_documents(texts)
        
        # Save each chunk and its embedding to pgvector
        for i, (chunk, embedding) in enumerate(zip(final_chunks, embeddings)):
            db_embedding = ResumeEmbedding(
                resume_id=resume_id,
                chunk_index=i,
                content=chunk.page_content,
                embedding=embedding
            )
            db_session.add(db_embedding)
            
        db_session.commit()

    def process_pdf(self, db_session, resume_id: int, pdf_path: str) -> None:
        """Processes a PDF file through the entire RAG ingestion pipeline.
        This orchestrator converts the PDF to Markdown, chunks it structure-aware,
        generates text embeddings, and saves them to PostgreSQL pgvector.
        """
        markdown_text = self.convert_to_markdown(pdf_path)
        final_chunks = self.get_structured_docs(markdown_text)
        self.save_to_postgres(db_session, resume_id, final_chunks)

