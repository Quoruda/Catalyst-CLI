from tools.bash import execute_bash
from tools.pdf import read_pdf

available_tools = {
    "execute_bash": execute_bash,
    "read_pdf": read_pdf
}

tools_schema = [
    {
        "name": "execute_bash",
        "description": "Executes a bash command on the local machine and returns the stdout, stderr, and exit code.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute."
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "read_pdf",
        "description": "Reads a local PDF file and returns its content in markdown format.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The path to the local PDF file."
                },
                "page_range": {
                    "type": "string",
                    "description": "Optional page number or range (e.g. '2', '1-3', '2,4')."
                }
            },
            "required": ["filepath"]
        }
    }
]
