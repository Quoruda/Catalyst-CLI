import os
import markdown

def compile_report(markdown_filepath: str, output_filepath: str = None) -> str:
    if not os.path.exists(markdown_filepath):
        return f"Error: Markdown file not found at {markdown_filepath}"
        
    if not output_filepath:
        output_filepath = markdown_filepath.rsplit('.', 1)[0] + ".html"
        
    try:
        with open(markdown_filepath, 'r', encoding='utf-8') as f:
            md_content = f.read()
            
        html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'toc'])
        
        css = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&family=Open+Sans:wght@400;600&display=swap');
            body { font-family: 'Open Sans', sans-serif; line-height: 1.6; color: #333; max-width: 850px; margin: 0 auto; padding: 40px; background-color: #fcfcfc; }
            h1, h2, h3 { font-family: 'Merriweather', serif; color: #111; border-bottom: 1px solid #eaeaea; padding-bottom: 0.3em; }
            h1 { font-size: 2.5em; text-align: center; margin-bottom: 1em; }
            h2 { font-size: 1.8em; margin-top: 1.5em; }
            p { margin-bottom: 1.2em; text-align: justify; }
            table { width: 100%; border-collapse: collapse; margin: 2em 0; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #f5f5f5; font-weight: 600; }
            tr:nth-child(even) { background-color: #fafafa; }
            blockquote { border-left: 4px solid #ccc; margin: 1.5em 0; padding-left: 1em; font-style: italic; color: #555; }
            @media print {
                body { padding: 0; background-color: #fff; }
                h1, h2 { page-break-after: avoid; }
                table, blockquote { page-break-inside: avoid; }
            }
        </style>
        """
        
        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Professional Report</title>
    {css}
</head>
<body>
    {html_body}
</body>
</html>"""

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(full_html)
            
        return f"Success! Beautiful HTML report compiled and saved to: {output_filepath}. The user can open it in any browser and print to PDF."
    except Exception as e:
        return f"Error compiling report: {str(e)}"

schema = {
    "name": "compile_report",
    "description": "Compiles a Markdown file into a beautiful, professional, print-ready HTML report with corporate CSS styling.",
    "parameters": {
        "type": "object",
        "properties": {
            "markdown_filepath": {
                "type": "string",
                "description": "Absolute path to the markdown file to compile."
            },
            "output_filepath": {
                "type": "string",
                "description": "Optional absolute path to the output HTML file. If not provided, it will save alongside the markdown file."
            }
        },
        "required": ["markdown_filepath"]
    }
}
