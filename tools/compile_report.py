import os
import re
import uuid
import shutil
import tempfile
import subprocess
import markdown

def compile_report(markdown_filepath: str, output_filepath: str = None) -> str:
    if not os.path.exists(markdown_filepath):
        return f"Error: Markdown file not found at {markdown_filepath}"
        
    if not output_filepath:
        output_filepath = markdown_filepath.rsplit('.', 1)[0] + ".html"
        
    output_ext = output_filepath.rsplit('.', 1)[-1].lower() if '.' in output_filepath else 'html'
    
    # Store all temp files in /tmp/catalyst_compile_[uuid]
    session_id = str(uuid.uuid4())[:8]
    temp_dir = os.path.join(tempfile.gettempdir(), f"catalyst_compile_{session_id}")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        with open(markdown_filepath, 'r', encoding='utf-8') as f:
            md_content = f.read()
            
        # Extract title dynamically from the first H1 in Markdown
        title = "Report"
        title_match = re.search(r'^#\s+(.+)$', md_content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
        else:
            # Fallback to filename formatted nicely
            title = os.path.basename(markdown_filepath).rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
            
        # Parse and process Mermaid code blocks
        # Pattern: ```mermaid \n [code] \n ```
        pattern = re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL)
        
        count = 0
        def replace_mermaid(match):
            nonlocal count
            count += 1
            mermaid_code = match.group(1).strip()
            
            # Write to a temp mmd file in /tmp/catalyst_compile_...
            temp_mmd_path = os.path.join(temp_dir, f"diagram_{count}.mmd")
            with open(temp_mmd_path, 'w', encoding='utf-8') as temp_mmd:
                temp_mmd.write(mermaid_code)
                
            img_filename = f"diagram_{count}.png"
            img_path = os.path.join(temp_dir, img_filename)
            
            # Execute mmdc with neutral theme and solid white background for high readability
            mmdc_success = False
            error_msg = ""
            
            # Find local workspace bin if exists
            local_bin = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "node_modules", ".bin", "mmdc"))
            
            commands_to_try = []
            if os.path.exists(local_bin):
                commands_to_try.append([local_bin, "-i", temp_mmd_path, "-o", img_path, "-t", "neutral", "-b", "white"])
            commands_to_try.extend([
                ["npx", "-y", "@mermaid-js/mermaid-cli", "-i", temp_mmd_path, "-o", img_path, "-t", "neutral", "-b", "white"],
                ["mmdc", "-i", temp_mmd_path, "-o", img_path, "-t", "neutral", "-b", "white"]
            ])
            
            for cmd in commands_to_try:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0 and os.path.exists(img_path):
                        mmdc_success = True
                        break
                    else:
                        error_msg = result.stderr or result.stdout
                except FileNotFoundError:
                    continue
                except Exception as e:
                    error_msg = str(e)
                    
            if mmdc_success:
                # Return standard markdown image referencing the temp image path (file:// URL so renderers accept it)
                return f"![Mermaid Diagram {count}](file://{img_path})"
            else:
                # Fallback to comment
                return f"<!-- Failed to compile Mermaid Diagram {count}: {error_msg} -->\n{match.group(0)}"
                
        processed_md = pattern.sub(replace_mermaid, md_content)
        
        # Convert processed Markdown to HTML
        html_body = markdown.markdown(processed_md, extensions=['tables', 'fenced_code', 'toc'])
        
        css = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&family=Open+Sans:wght@400;600&display=swap');
            body { font-family: 'Open Sans', sans-serif; line-height: 1.6; color: #333; max-width: 850px; margin: 0 auto; padding: 40px; background-color: #fcfcfc; }
            h1, h2, h3 { font-family: 'Merriweather', serif; color: #111; border-bottom: 1px solid #eaeaea; padding-bottom: 0.3em; }
            h1 { font-size: 2.5em; text-align: center; margin-bottom: 1em; }
            h2 { font-size: 1.8em; margin-top: 1.5em; }
            p { margin-bottom: 1.2em; text-align: justify; }
            img { max-width: 100%; height: auto; display: block; margin: 1.5em auto; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
            table { width: 100%; border-collapse: collapse; margin: 2em 0; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #f5f5f5; font-weight: 600; }
            tr:nth-child(even) { background-color: #fafafa; }
            blockquote { border-left: 4px solid #ccc; margin: 1.5em 0; padding-left: 1em; font-style: italic; color: #555; }
            @media print {
                body { padding: 0; background-color: #fff; }
                h1, h2 { page-break-after: avoid; }
                table, blockquote, img { page-break-inside: avoid; }
            }
        </style>
        """
        
        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    {css}
</head>
<body>
    {html_body}
</body>
</html>"""

        # If compiling to HTML
        if output_ext == 'html':
            output_dir = os.path.dirname(os.path.abspath(output_filepath))
            
            # Find all temp image paths and copy them to output dir
            temp_images = [f for f in os.listdir(temp_dir) if f.endswith('.png')]
            for img in temp_images:
                shutil.copy(os.path.join(temp_dir, img), os.path.join(output_dir, img))
                
            # Replace file:// absolute temp paths with relative paths in HTML
            relative_html = full_html.replace(f"file://{temp_dir}/", "")
            
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(relative_html)
            return f"Success! Beautiful HTML report compiled and saved to: {output_filepath}. Mermaid diagrams were rendered as local PNGs."

        # If compiling to PDF
        elif output_ext == 'pdf':
            # Save HTML inside temp dir
            temp_html_path = os.path.join(temp_dir, "report.html")
            with open(temp_html_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
                
            pdf_success = False
            error_details = []
            
            # Try WeasyPrint first
            try:
                import weasyprint
                weasyprint.HTML(temp_html_path).write_pdf(output_filepath)
                pdf_success = True
            except ImportError:
                error_details.append("WeasyPrint library not installed (pip install weasyprint).")
            except Exception as e:
                error_details.append(f"WeasyPrint failed: {str(e)}")
                
            # Try Headless Chrome/Chromium next if WeasyPrint failed (with no header/footer flag to hide date/time/title)
            if not pdf_success:
                chrome_commands = ["google-chrome", "chromium-browser", "chromium"]
                for cmd in chrome_commands:
                    try:
                        exec_cmd = [cmd, "--headless", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer", f"--print-to-pdf={output_filepath}", temp_html_path]
                        result = subprocess.run(exec_cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            pdf_success = True
                            break
                    except FileNotFoundError:
                        continue
                    except Exception as e:
                        error_details.append(f"{cmd} failed: {str(e)}")
                        
            if pdf_success:
                return f"Success! Beautiful PDF report compiled and saved to: {output_filepath}. Mermaid diagrams were rendered locally."
            else:
                # Fallback: Save HTML instead and alert user
                html_fallback = output_filepath.rsplit('.', 1)[0] + ".html"
                
                # Copy images to output folder
                output_dir = os.path.dirname(os.path.abspath(html_fallback))
                temp_images = [f for f in os.listdir(temp_dir) if f.endswith('.png')]
                for img in temp_images:
                    shutil.copy(os.path.join(temp_dir, img), os.path.join(output_dir, img))
                relative_html = full_html.replace(f"file://{temp_dir}/", "")
                
                with open(html_fallback, 'w', encoding='utf-8') as f:
                    f.write(relative_html)
                errors_str = " | ".join(error_details)
                return f"Warning: Failed to compile to PDF ({errors_str}). Saved HTML fallback instead at: {html_fallback}. You can open it in any browser and print to PDF."
                
        else:
            return f"Error: Unsupported output format: .{output_ext}. Supported formats are .html and .pdf."
            
    except Exception as e:
        return f"Error compiling report: {str(e)}"
    finally:
        # Always clean up the temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

schema = {
    "name": "compile_report",
    "description": "Compiles a Markdown file into a beautiful, professional, print-ready HTML or PDF report, rendering Mermaid diagrams locally as PNGs.",
    "parameters": {
        "type": "object",
        "properties": {
            "markdown_filepath": {
                "type": "string",
                "description": "Absolute path to the markdown file to compile."
            },
            "output_filepath": {
                "type": "string",
                "description": "Optional absolute path to the output HTML or PDF file. If not provided, it will save alongside the markdown file with .html extension."
            }
        },
        "required": ["markdown_filepath"]
    }
}
