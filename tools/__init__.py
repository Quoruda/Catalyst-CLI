from tools.bash import execute_bash
from tools.pdf import read_pdf

available_tools = {
    "execute_bash": execute_bash,
    "read_pdf": read_pdf
}

tools_description = """
execute_bash(command: str) -> str
Executes a bash command on the local machine and returns the stdout, stderr, and exit code.

read_pdf(filepath: str, page_range: str = None) -> str
Reads a local PDF file and returns its content in markdown format.
Arguments should be comma-separated: filepath, and optionally a page number or range (e.g. "2", "1-3", "2,4").
Example: read_pdf[document.pdf] or read_pdf[document.pdf, 2] or read_pdf[document.pdf, 1-3]
If page_range is omitted and the PDF has more than 3 pages, it returns the first page and a guide on how to request other pages.
"""
