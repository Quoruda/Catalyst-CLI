import os
import sys
import contextlib
import fitz
import pymupdf4llm

@contextlib.contextmanager
def silence_all():
    new_stdout = open(os.devnull, 'w')
    new_stderr = open(os.devnull, 'w')
    old_stdout_fd = os.dup(1)
    old_stderr_fd = os.dup(2)
    try:
        os.dup2(new_stdout.fileno(), 1)
        os.dup2(new_stderr.fileno(), 2)
        with contextlib.redirect_stdout(new_stdout), contextlib.redirect_stderr(new_stderr):
            yield
    finally:
        os.dup2(old_stdout_fd, 1)
        os.dup2(old_stderr_fd, 2)
        os.close(old_stdout_fd)
        os.close(old_stderr_fd)
        new_stdout.close()
        new_stderr.close()

def read_pdf(filepath: str, page_range: str = None) -> str:
    if not os.path.exists(filepath):
        return f"Error: File not found: {filepath}"
        
    try:
        doc = fitz.open(filepath)
        num_pages = len(doc)
        
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
                
            with silence_all():
                content = pymupdf4llm.to_markdown(filepath, pages=pages_to_read)
            return content
            
        meta = doc.metadata
        metadata_str = ", ".join(f"{k}: {v}" for k, v in meta.items() if v)
        
        if num_pages <= 3:
            with silence_all():
                markdown_content = pymupdf4llm.to_markdown(filepath)
            return f"Metadata: {metadata_str}\nTotal Pages: {num_pages}\n\n{markdown_content}"
        else:
            with silence_all():
                first_page_markdown = pymupdf4llm.to_markdown(filepath, pages=[0])
            return f"Metadata: {metadata_str}\nTotal Pages: {num_pages}\nDocument is large. To read specific pages, use: read_pdf[filepath, page_number] (e.g. read_pdf[file.pdf, 2] or read_pdf[file.pdf, 1-3])\n\n--- FIRST PAGE PREVIEW ---\n{first_page_markdown}"
            
    except Exception as e:
        return f"Error reading PDF: {str(e)}"
