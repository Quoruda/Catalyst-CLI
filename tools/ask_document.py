import os
from providers import LiteLLMProvider
from config import AgentConfig

def ask_document(filepath: str, query: str) -> str:
    """Reads a document (PDF, MD, txt) and answers a specific query using the LLM."""
    if not os.path.exists(filepath):
        return f"Error: File not found: {filepath}"
        
    try:
        content = ""
        if filepath.lower().endswith('.pdf'):
            import fitz
            import pymupdf4llm
            from tools.pdf import silence_all
            
            doc = fitz.open(filepath)
            
            with silence_all():
                content = pymupdf4llm.to_markdown(filepath)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

        from magic import ask_llm
        
        system_prompt = "You are a document analyzer. Read the provided document and answer the user's query. Be precise and concise."
        user_prompt = f"--- DOCUMENT CONTENT ---\n{content}\n\n--- USER QUERY ---\n{query}"
        
        response_text = ask_llm(system_prompt, user_prompt)
        return f"Analysis Result:\n{response_text}"

    except ImportError as e:
        return f"Error: Missing dependency ({str(e)}). Try 'pip install pymupdf4llm litellm'"
    except Exception as e:
        return f"Error processing document: {str(e)}"

schema = {
    "name": "ask_document",
    "description": "Reads a local document (PDF, TXT, MD, etc.) and uses an AI to answer a specific question or summarize it internally. Use this tool instead of reading the file directly to save your context window.",
    "parameters": {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "The absolute path to the local document."
            },
            "query": {
                "type": "string",
                "description": "The exact question to ask about the document, or 'summarize' to get a general overview."
            }
        },
        "required": ["filepath", "query"]
    }
}
