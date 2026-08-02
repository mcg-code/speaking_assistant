import os
import uuid
import chromadb
from typing import List
from rich.console import Console

from services import llm_service
from core import prompts

console = Console()

_db_client = None
_collection = None

def get_chroma_client():
    global _db_client, _collection
    if _db_client is None:
        # Hide chroma logs if possible
        os.environ["CHROMA_LOG_LEVEL"] = "error"
        
        # Store DB in a hidden folder inside the project
        db_path = os.path.join(os.getcwd(), ".chroma_db")
        _db_client = chromadb.PersistentClient(path=db_path)
        # Using default embedding function (all-MiniLM-L6-v2)
        _collection = _db_client.get_or_create_collection(name="student_mistakes")
    return _collection

def store_mistakes(model_name: str, feedback_text: str) -> None:
    """
    Extracts core mistakes from the feedback text using Ollama and stores them in ChromaDB.
    """
    if not feedback_text.strip():
        return
        
    try:
        console.print("[dim]Extracting core mistakes for long-term memory...[/dim]")
        # 1. Ask Ollama to extract bullet points
        prompt = prompts.EXTRACTION_PROMPT.format(feedback=feedback_text)
        
        messages = [{'role': 'user', 'content': prompt}]
        extraction = llm_service.chat(model_name, messages)
        
        # 2. Parse bullet points
        mistakes = []
        for line in extraction.split('\n'):
            line = line.strip()
            if line.startswith('-') or line.startswith('*'):
                clean_line = line.lstrip('-* ').strip()
                if clean_line:
                    mistakes.append(clean_line)
                    
        if not mistakes:
            return
            
        # 3. Store in ChromaDB
        collection = get_chroma_client()
        
        ids = [str(uuid.uuid4()) for _ in mistakes]
        metadatas = [{"source": "feedback"} for _ in mistakes]
        
        collection.add(
            documents=mistakes,
            metadatas=metadatas,
            ids=ids
        )
        console.print(f"[green]Stored {len(mistakes)} mistakes in long-term memory.[/green]")
        
    except Exception as e:
        console.print(f"[red]Failed to store mistakes in memory: {e}[/red]")

def get_relevant_mistakes_text() -> str:
    """
    Queries ChromaDB for recent or relevant mistakes and formats them for the prompt.
    """
    try:
        collection = get_chroma_client()
        
        # Check if collection is empty
        if collection.count() == 0:
            return ""
            
        # We query for general mistakes to get the most relevant ones.
        # Since we want to inject weak points, a broad query works well.
        results = collection.query(
            query_texts=["grammar mistake vocabulary error pronunciation correction"],
            n_results=5
        )
        
        if not results['documents'] or not results['documents'][0]:
            return ""
            
        mistakes = results['documents'][0]
        
        formatted_mistakes = "\nIMPORTANT INSTRUCTION: Pay special attention to these past mistakes the student makes often:\n"
        for m in mistakes:
            formatted_mistakes += f"- {m}\n"
            
        return formatted_mistakes
        
    except Exception as e:
        return ""
