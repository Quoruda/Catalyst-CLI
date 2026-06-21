import os
import re
import uuid
import shutil
import tempfile
import subprocess
import markdown

def add_page_numbers(pdf_path: str):
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    import io
    
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    num_pages = len(reader.pages)
    
    for page_idx in range(num_pages):
        page = reader.pages[page_idx]
        
        # Get page dimensions dynamically (handles portrait and landscape)
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        
        # Create a temp PDF in memory with the page number
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))
        can.setFont("Helvetica", 8)
        can.setFillColorRGB(0.5, 0.5, 0.5)  # Subtle gray color
        text = f"{page_idx + 1} / {num_pages}"
        # Position page number at bottom center (approx 12mm / 34pt from bottom)
        can.drawCentredString(width / 2.0, 34, text)
        can.save()
        
        # Overlay the page number onto the original page
        packet.seek(0)
        num_reader = PdfReader(packet)
        num_page = num_reader.pages[0]
        page.merge_page(num_page)
        writer.add_page(page)
        
    with open(pdf_path, 'wb') as f:
        writer.write(f)

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
        # Create a custom CSS file to force dark text/borders on Mermaid diagrams.
        # We target body, div, span, p, text, and foreignObject elements to override dark-mode defaults.
        css_theme_path = os.path.join(temp_dir, "mermaid_theme.css")
        with open(css_theme_path, 'w', encoding='utf-8') as f:
            f.write("""
            /* Force dark text and clean strokes for readability in reports */
            body, div, span, p, text, .label, .nodeText, .labelText, .actor, .messageText, .loopText {
                color: #111111 !important;
                fill: #111111 !important;
            }
            .node rect, .node circle, .node ellipse, .node polygon, .node path {
                stroke: #222222 !important;
                stroke-width: 1.5px !important;
            }
            .edgePath .path {
                stroke: #222222 !important;
                stroke-width: 1.5px !important;
            }
            .edgeLabel rect {
                fill: #ffffff !important;
            }
            .cluster rect {
                fill: #fcfcfc !important;
                stroke: #bbbbbb !important;
            }
            """)
            
        # Create a mermaid config file to enforce the default/neutral theme and override color scheme variables
        config_path = os.path.join(temp_dir, "mermaid_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("""
            {
              "theme": "neutral",
              "themeVariables": {
                "background": "#ffffff",
                "textColor": "#111111",
                "nodeTextColor": "#111111",
                "lineColor": "#222222",
                "primaryColor": "#f5f5f5",
                "edgeLabelBackground": "#ffffff"
              },
              "themeCSS": "div, span, p, text, .label, .nodeText, .labelText { color: #111111 !important; fill: #111111 !important; } .node rect, .node circle, .node ellipse, .node polygon, .node path { stroke: #222222 !important; } .edgePath .path { stroke: #222222 !important; }"
            }
            """)
            
        with open(markdown_filepath, 'r', encoding='utf-8') as f:
            md_content = f.read()
            
        # Strip the date line at the top during generation (e.g. **Date :** ... or Date : ...)
        md_content = re.sub(r'^\s*\**Date\s*:\**\s*.*$', '', md_content, flags=re.MULTILINE | re.IGNORECASE)
        
        # Resolve relative image paths to absolute file:// URLs.
        # This prevents breaking images during compilation since renderers run from different working directories.
        markdown_dir = os.path.dirname(os.path.abspath(markdown_filepath))
        
        # 1. Resolve markdown images: ![alt](path)
        img_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
        def replace_image_path(match):
            alt_text = match.group(1)
            img_path = match.group(2).strip()
            if img_path.startswith(('http://', 'https://', 'file://', '/')):
                return match.group(0)
            abs_img_path = os.path.abspath(os.path.join(markdown_dir, img_path))
            return f"![{alt_text}](file://{abs_img_path})"
        md_content = img_pattern.sub(replace_image_path, md_content)
        
        # 2. Resolve HTML images: <img src="path" ...>
        html_img_pattern = re.compile(r'<img\s+([^>]*?)src=["\'](.*?)["\']([^>]*?)>', re.IGNORECASE)
        def replace_html_image_path(match):
            prefix = match.group(1)
            img_path = match.group(2).strip()
            suffix = match.group(3)
            if img_path.startswith(('http://', 'https://', 'file://', '/')):
                return match.group(0)
            abs_img_path = os.path.abspath(os.path.join(markdown_dir, img_path))
            return f'<img {prefix}src="file://{abs_img_path}"{suffix}>'
        md_content = html_img_pattern.sub(replace_html_image_path, md_content)
            
        # Extract title dynamically from the first H1 in Markdown
        title = "Report"
        title_match = re.search(r'^#\s+(.+)$', md_content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
        else:
            title = os.path.basename(markdown_filepath).rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
            
        # Parse and process Mermaid code blocks
        pattern = re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL)
        
        count = 0
        def replace_mermaid(match):
            nonlocal count
            count += 1
            mermaid_code = match.group(1).strip()
            
            # Write to a temp mmd file
            temp_mmd_path = os.path.join(temp_dir, f"diagram_{count}.mmd")
            with open(temp_mmd_path, 'w', encoding='utf-8') as temp_mmd:
                temp_mmd.write(mermaid_code)
                
            img_filename = f"diagram_{count}.png"
            img_path = os.path.join(temp_dir, img_filename)
            
            # Execute mmdc with config, CSS override, and white background
            mmdc_success = False
            error_msg = ""
            
            # Find local workspace bin if exists
            local_bin = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "node_modules", ".bin", "mmdc"))
            
            commands_to_try = []
            if os.path.exists(local_bin):
                commands_to_try.append([local_bin, "-i", temp_mmd_path, "-o", img_path, "-b", "white", "-c", config_path, "-C", css_theme_path])
            commands_to_try.extend([
                ["npx", "-y", "@mermaid-js/mermaid-cli", "-i", temp_mmd_path, "-o", img_path, "-b", "white", "-c", config_path, "-C", css_theme_path],
                ["mmdc", "-i", temp_mmd_path, "-o", img_path, "-b", "white", "-c", config_path, "-C", css_theme_path]
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
                return f"![Mermaid Diagram {count}](file://{img_path})"
            else:
                return f"<!-- Failed to compile Mermaid Diagram {count}: {error_msg} -->\n{match.group(0)}"
                
        processed_md = pattern.sub(replace_mermaid, md_content)
        
        # Convert processed Markdown to HTML (using the 'toc' extension)
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
            
            /* Table of Contents Styling */
            .toc {
                background-color: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 20px;
                margin: 2em 0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                page-break-after: always;
            }
            .toc ul {
                list-style-type: none;
                padding-left: 20px;
            }
            .toc ul li {
                margin-bottom: 0.5em;
            }
            .toc a {
                color: #1a73e8;
                text-decoration: none;
            }
            .toc a:hover {
                text-decoration: underline;
            }
            
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
            
            # Copy all temp images generated by mermaid to the output directory
            temp_images = [f for f in os.listdir(temp_dir) if f.endswith('.png')]
            for img in temp_images:
                shutil.copy(os.path.join(temp_dir, img), os.path.join(output_dir, img))
                
            # Convert file:// absolute paths back to relative references
            def make_path_relative(match):
                path = match.group(1)
                if path.startswith(temp_dir):
                    filename = os.path.basename(path)
                    return f'src="{filename}"'
                rel_path = os.path.relpath(path, output_dir)
                return f'src="{rel_path}"'
                
            relative_html = re.sub(r'src="file://(/[^\s"\']*)"', make_path_relative, full_html)
            
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(relative_html)
            return f"Success! Beautiful HTML report compiled and saved to: {output_filepath}. Mermaid diagrams were rendered as local PNGs."

        # If compiling to PDF
        elif output_ext == 'pdf':
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
                
            # Try Headless Chrome/Chromium next if WeasyPrint failed
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
                # Dynamically apply page numbers using pypdf and reportlab
                try:
                    add_page_numbers(output_filepath)
                except Exception as pe:
                    return f"Success! Beautiful PDF report compiled and saved to: {output_filepath}. (Note: page numbering post-processing failed: {pe})"
                return f"Success! Beautiful PDF report compiled and saved to: {output_filepath}. Mermaid diagrams were rendered locally and page numbers were added."
            else:
                html_fallback = output_filepath.rsplit('.', 1)[0] + ".html"
                output_dir = os.path.dirname(os.path.abspath(html_fallback))
                temp_images = [f for f in os.listdir(temp_dir) if f.endswith('.png')]
                for img in temp_images:
                    shutil.copy(os.path.join(temp_dir, img), os.path.join(output_dir, img))
                
                def make_path_relative_fallback(match):
                    path = match.group(1)
                    if path.startswith(temp_dir):
                        filename = os.path.basename(path)
                        return f'src="{filename}"'
                    rel_path = os.path.relpath(path, output_dir)
                    return f'src="{rel_path}"'
                relative_html = re.sub(r'src="file://(/[^\s"\']*)"', make_path_relative_fallback, full_html)
                
                with open(html_fallback, 'w', encoding='utf-8') as f:
                    f.write(relative_html)
                errors_str = " | ".join(error_details)
                return f"Warning: Failed to compile to PDF ({errors_str}). Saved HTML fallback instead at: {html_fallback}."
                
        else:
            return f"Error: Unsupported output format: .{output_ext}."
            
    except Exception as e:
        return f"Error compiling report: {str(e)}"
    finally:
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
