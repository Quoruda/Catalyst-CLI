import subprocess
import os

def read_clipboard() -> str:
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
        return subprocess.check_output(['wl-paste']).decode('utf-8')
    except Exception:
        pass
        
    # Fallback X11 (xclip)
    try:
        return subprocess.check_output(['xclip', '-selection', 'clipboard', '-o']).decode('utf-8')
    except Exception as e:
        return f"Error reading clipboard. Make sure xclip or wl-clipboard is installed. Details: {e}"

def write_clipboard(text: str) -> str:
    # Try pyperclip first
    try:
        import pyperclip
        pyperclip.copy(text)
        return "Successfully copied to clipboard."
    except ImportError:
        pass
        
    # Fallback Wayland (wl-copy)
    try:
        p = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE)
        p.communicate(input=text.encode('utf-8'))
        if p.returncode == 0:
            return "Successfully copied to clipboard (using wl-copy)."
    except Exception:
        pass
        
    # Fallback X11 (xclip)
    try:
        p = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
        p.communicate(input=text.encode('utf-8'))
        if p.returncode == 0:
            return "Successfully copied to clipboard (using xclip)."
    except Exception as e:
        return f"Error writing to clipboard. Make sure xclip or wl-clipboard is installed. Details: {e}"

schema = {
    "name": "clipboard_manager",
    "description": "Reads text from or writes text to the user's system clipboard.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "write"],
                "description": "The action to perform: 'read' to get the current clipboard contents, 'write' to set new contents."
            },
            "content": {
                "type": "string",
                "description": "The exact text to write to the clipboard. Must be provided if action is 'write'. Omit if action is 'read'."
            }
        },
        "required": ["action"],
        "additionalProperties": False
    }
}

def clipboard_manager(action: str, content: str = "") -> str:
    if action == "read":
        res = read_clipboard()
        if not res.strip():
            return "Clipboard is currently empty."
        return res
    elif action == "write":
        if not content:
            return "Error: you must provide the 'content' parameter to write to the clipboard."
        return write_clipboard(content)
    else:
        return f"Error: unknown action '{action}'. Must be 'read' or 'write'."
