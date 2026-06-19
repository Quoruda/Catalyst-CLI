import os
import re

def read_file(filepath: str) -> str:
    """Reads the content of a local text file."""
    if not os.path.exists(filepath):
        return f"Error: File '{filepath}' does not exist."
    try:
        size = os.path.getsize(filepath)
        if size > 500 * 1024:  # 500 KB limit
            return f"Error: File '{filepath}' is too large ({size} bytes). Max readable size is 500KB."
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        return f"Error: File '{filepath}' is a binary file or does not use UTF-8 encoding."
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(filepath: str, content: str) -> str:
    """Writes content to a file, creating parent directories if they don't exist."""
    try:
        parent = os.path.dirname(filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{filepath}' written successfully."
    except Exception as e:
        return f"Error writing file: {str(e)}"

def append_file(filepath: str, content: str) -> str:
    """Appends content to the end of a file, creating it if it doesn't exist."""
    try:
        parent = os.path.dirname(filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content)
        return f"Content appended successfully to '{filepath}'."
    except Exception as e:
        return f"Error appending to file: {str(e)}"

def patch_file(filepath: str, patch: str) -> str:
    """Applies one or more SEARCH/REPLACE blocks to a file."""
    if not os.path.exists(filepath):
        return f"Error: File '{filepath}' does not exist."
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        pattern = re.compile(
            r'^<{5,}\s*(?:SEARCH)?\r?\n(.*?)\r?\n={5,}\r?\n(.*?)\r?\n>{5,}\s*(?:REPLACE)?',
            re.MULTILINE | re.DOTALL | re.IGNORECASE
        )
        
        blocks = pattern.findall(patch)
        if not blocks:
            return ("Error: No valid SEARCH/REPLACE blocks found in the patch.\n"
                    "Make sure you use the exact format:\n"
                    "<<<<<<< SEARCH\n"
                    "<code to search for>\n"
                    "=======\n"
                    "<replacement code>\n"
                    ">>>>>>> REPLACE")
        
        new_content = content
        for idx, (search_block, replace_block) in enumerate(blocks, 1):
            occurrences = new_content.count(search_block)
            if occurrences == 0:
                return (f"Error in patch block #{idx}: The SEARCH block was not found in '{filepath}'.\n"
                        f"Make sure indentation, spaces, and newlines match the file exactly.\n"
                        f"SEARCH block attempted:\n{search_block}")
            if occurrences > 1:
                return (f"Error in patch block #{idx}: The SEARCH block is not unique (found {occurrences} times).\n"
                        f"Please add more surrounding lines in the SEARCH block to uniquely identify the block to replace.")
                
            new_content = new_content.replace(search_block, replace_block, 1)
            
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        return f"Successfully applied {len(blocks)} patch block(s) to '{filepath}'."
    except Exception as e:
        return f"Error patching file: {str(e)}"

# Schemas for agent discovery
read_file_schema = {
    "name": "read_file",
    "description": "Reads the complete contents of a text file from the local filesystem.",
    "parameters": {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "The absolute or relative path to the file to read."
            }
        },
        "required": ["filepath"]
    }
}

write_file_schema = {
    "name": "write_file",
    "description": "Creates a new file or overwrites an existing file with the specified content. Automatically creates parent directories.",
    "parameters": {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "The absolute or relative path to the file to write."
            },
            "content": {
                "type": "string",
                "description": "The complete content to write into the file."
            }
        },
        "required": ["filepath", "content"]
    }
}

append_file_schema = {
    "name": "append_file",
    "description": "Appends text directly to the end of an existing file (or creates it if it doesn't exist). Extremely useful and efficient for writing documents section by section.",
    "parameters": {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "The absolute or relative path to the file."
            },
            "content": {
                "type": "string",
                "description": "The content to append to the end of the file."
            }
        },
        "required": ["filepath", "content"]
    }
}

patch_file_schema = {
    "name": "patch_file",
    "description": (
        "Modifies an existing file by applying one or more SEARCH/REPLACE blocks. "
        "Use this instead of write_file for editing large files. "
        "The patch format must be one or more blocks like:\n"
        "<<<<<<< SEARCH\n"
        "<exact lines from the original file to replace>\n"
        "=======\n"
        "<replacement lines>\n"
        ">>>>>>> REPLACE"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "The absolute or relative path to the file to patch."
            },
            "patch": {
                "type": "string",
                "description": "One or more SEARCH/REPLACE blocks specifying the modifications to apply."
            }
        },
        "required": ["filepath", "patch"]
    }
}

schemas = [read_file_schema, write_file_schema, append_file_schema, patch_file_schema]
