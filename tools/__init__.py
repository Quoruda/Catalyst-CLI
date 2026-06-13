from tools.bash import execute_bash
from tools.pdf import read_pdf
from tools.vision import view_image

available_tools = {
    "execute_bash": execute_bash,
    "read_pdf": read_pdf,
    "view_image": view_image
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
    },
    {
        "name": "view_image",
        "description": "Analyzes a local image file (PNG, JPG, WEBP, GIF) using the multimodal LLM and returns the description or analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The path to the local image file."
                },
                "prompt": {
                    "type": "string",
                    "description": "Optional prompt to guide the model's analysis (e.g. 'Read the text in this image' or 'What color is the car?')."
                }
            },
            "required": ["filepath"]
        }
    }
]
