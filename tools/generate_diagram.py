import os
import tempfile
import subprocess

def execute(diagram_type: str, source_code: str, output_path: str, **kwargs):
    """
    Generates a diagram image from source code using local mermaid-cli (mmdc).
    """
    if diagram_type.lower() != 'mermaid':
        return f"Error: Local diagram generation currently only supports 'mermaid'. You requested '{diagram_type}'."
        
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(os.path.abspath(output_path))
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        # Create a temporary file for the mermaid source code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as temp_in:
            temp_in.write(source_code)
            temp_in_path = temp_in.name
            
        # Call local mmdc (Mermaid CLI)
        cmd = ["mmdc", "-i", temp_in_path, "-o", output_path, "-b", "transparent"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up temp file
        if os.path.exists(temp_in_path):
            os.remove(temp_in_path)
            
        if process.returncode != 0:
            return f"Failed to generate diagram using mmdc.\nError output: {process.stderr}"
            
        return f"Diagram successfully generated locally and saved as an image at: {output_path}"
        
    except FileNotFoundError:
        return "Failed to find 'mmdc' command. The system requires mermaid-cli to be installed locally. The user must run: npm install -g @mermaid-js/mermaid-cli"
    except Exception as e:
        return f"Error generating diagram: {str(e)}"

SCHEMA = {
    "name": "generate_diagram",
    "description": "Generates a clean diagram image (PNG) from text source code (Mermaid ONLY) using local rendering, and saves it to the specified output path. The image can then be embedded in Markdown files.",
    "parameters": {
        "type": "object",
        "properties": {
            "diagram_type": {
                "type": "string",
                "description": "The diagram syntax type. MUST be 'mermaid'."
            },
            "source_code": {
                "type": "string",
                "description": "The actual diagram source code (e.g. 'graph TD\\n A-->B'). Do not include markdown code block backticks."
            },
            "output_path": {
                "type": "string",
                "description": "The absolute or relative path where the PNG image should be saved (e.g. './docs/architecture.png')."
            }
        },
        "required": ["diagram_type", "source_code", "output_path"]
    }
}
