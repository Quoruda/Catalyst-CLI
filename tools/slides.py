import os
import subprocess

def compile_presentation(markdown_path: str, output_format: str = "html", custom_theme_path: str = "") -> str:
    if not os.path.exists(markdown_path):
        return f"Error: Markdown file not found at {markdown_path}"
        
    ext = output_format.lower()
    if ext not in ["html", "pdf", "pptx"]:
        ext = "html"
        
    output_path = os.path.splitext(markdown_path)[0] + f".{ext}"
    
    cmd = [
        "npx", "-y", "@marp-team/marp-cli@latest",
        markdown_path,
        "-o", output_path,
        "--html" 
    ]
    
    if custom_theme_path and os.path.exists(custom_theme_path):
        cmd.extend(["--theme", custom_theme_path])
        
    try:
        # Running via shell=False
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return f"Successfully compiled presentation to {output_path}"
    except subprocess.CalledProcessError as e:
        return f"Error compiling presentation: {e.stderr or e.stdout}"

schema_compile_presentation = {
    "name": "compile_presentation",
    "description": "Compiles a Markdown file into a professional presentation (HTML, PDF, or PPTX) using Marp.",
    "parameters": {
        "type": "object",
        "properties": {
            "markdown_path": {
                "type": "string",
                "description": "Absolute path to the Markdown file containing the slides."
            },
            "output_format": {
                "type": "string",
                "enum": ["html", "pdf", "pptx"],
                "description": "The desired output format (default is html). HTML is highly recommended for animations and web viewing."
            },
            "custom_theme_path": {
                "type": "string",
                "description": "Optional path to a custom CSS theme file."
            }
        },
        "required": ["markdown_path"]
    }
}

schemas = [schema_compile_presentation]
