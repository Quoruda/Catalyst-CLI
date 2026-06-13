import os
import fitz
import pymupdf4llm

def read_pdf(args: str) -> str:
    parts = [p.strip() for p in args.split(",")]
    filepath = parts[0].strip("'\"")
    
    if not os.path.exists(filepath):
        return f"Error: File not found: {filepath}"
        
    try:
        doc = fitz.open(filepath)
        num_pages = len(doc)
        
        page_range = None
        if len(parts) > 1:
            page_range = parts[1].strip()
            
        if page_range:
            pages_to_read = []
            if "-" in page_range:
                start, end = page_range.split("-")
                pages_to_read = list(range(int(start) - 1, int(end)))
            elif "," in page_range:
                pages_to_read = [int(p) - 1 for p in page_range.split(",")]
            else:
                pages_to_read = [int(page_range) - 1]
                
            pages_to_read = [p for p in pages_to_read if 0 <= p < num_pages]
            if not pages_to_read:
                return f"Error: Page range {page_range} is out of bounds for a document with {num_pages} pages."
                
            return pymupdf4llm.to_markdown(filepath, pages=pages_to_read)
            
        meta = doc.metadata
        metadata_str = ", ".join(f"{k}: {v}" for k, v in meta.items() if v)
        
        if num_pages <= 3:
            markdown_content = pymupdf4llm.to_markdown(filepath)
            return f"Metadata: {metadata_str}\nTotal Pages: {num_pages}\n\n{markdown_content}"
        else:
            first_page_markdown = pymupdf4llm.to_markdown(filepath, pages=[0])
            return f"Metadata: {metadata_str}\nTotal Pages: {num_pages}\nDocument is large. To read specific pages, use: read_pdf[filepath, page_number] (e.g. read_pdf[file.pdf, 2] or read_pdf[file.pdf, 1-3])\n\n--- FIRST PAGE PREVIEW ---\n{first_page_markdown}"
            
    except Exception as e:
        return f"Error reading PDF: {str(e)}"
