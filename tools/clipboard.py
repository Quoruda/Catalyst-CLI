import subprocess
import os
import tempfile

read_schema = {
    "name": "read_clipboard",
    "description": "Reads from the system clipboard. If it contains text, it returns the text. If it contains an image, it saves it to a temp file and returns instructions to view it.",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False
    }
}

write_schema = {
    "name": "write_clipboard",
    "description": "Writes text to the user's system clipboard.",
    "parameters": {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The exact text to write to the clipboard."
            }
        },
        "required": ["content"],
        "additionalProperties": False
    }
}

schemas = [read_schema, write_schema]

def check_and_save_image() -> str:
    # Try Wayland first
    try:
        types = subprocess.check_output(['wl-paste', '--list-types'], stderr=subprocess.DEVNULL).decode('utf-8')
        if 'image/png' in types or 'image/jpeg' in types:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            subprocess.check_call(['wl-paste', '--type', 'image/png'], stdout=tmp, stderr=subprocess.DEVNULL)
            tmp.close()
            return f"[Image detected in clipboard. Automatically saved to: {tmp.name}. Please use your 'view_image' tool on this path to analyze it.]"
    except Exception:
        pass
        
    # Try X11
    try:
        types = subprocess.check_output(['xclip', '-selection', 'clipboard', '-t', 'TARGETS', '-o'], stderr=subprocess.DEVNULL).decode('utf-8')
        if 'image/png' in types or 'image/jpeg' in types:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            subprocess.check_call(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-o'], stdout=tmp, stderr=subprocess.DEVNULL)
            tmp.close()
            return f"[Image detected in clipboard. Automatically saved to: {tmp.name}. Please use your 'view_image' tool on this path to analyze it.]"
    except Exception:
        pass
        
    return ""

def read_clipboard() -> str:
    image_msg = check_and_save_image()
    if image_msg:
        return image_msg
        
    # Try pyperclip first
    try:
        import pyperclip
        content = pyperclip.paste()
        if content:
            return content
    except ImportError:
        pass
        
    # Fallback Wayland (wl-paste)
    try:
        content = subprocess.check_output(['wl-paste'], stderr=subprocess.DEVNULL).decode('utf-8')
        if content:
            return content
    except Exception:
        pass
        
    # Fallback X11 (xclip)
    try:
        content = subprocess.check_output(['xclip', '-selection', 'clipboard', '-o'], stderr=subprocess.DEVNULL).decode('utf-8')
        if content:
            return content
    except Exception as e:
        return f"Error reading clipboard. Make sure xclip or wl-clipboard is installed. Details: {e}"
        
    return "Clipboard is empty or contains unsupported data."

def write_clipboard(content: str) -> str:
    # Try pyperclip first
    try:
        import pyperclip
        pyperclip.copy(content)
        return "Successfully copied to clipboard."
    except ImportError:
        pass
        
    # Fallback Wayland (wl-copy)
    try:
        p = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE)
        p.communicate(input=content.encode('utf-8'))
        if p.returncode == 0:
            return "Successfully copied to clipboard (using wl-copy)."
    except Exception:
        pass
        
    # Fallback X11 (xclip)
    try:
        p = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
        p.communicate(input=content.encode('utf-8'))
        if p.returncode == 0:
            return "Successfully copied to clipboard (using xclip)."
    except Exception as e:
        return f"Error writing to clipboard. Make sure xclip or wl-clipboard is installed. Details: {e}"
