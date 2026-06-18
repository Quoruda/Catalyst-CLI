import os
from pathlib import Path

def generate_context_map(directory: str = ".", max_depth: int = 3, ignore_dirs: list = None) -> str:
    if ignore_dirs is None:
        ignore_dirs = [".git", "node_modules", "__pycache__", ".venv", "venv", "env", ".idea", ".vscode", "dist", "build"]
        
    start_path = Path(directory).resolve()
    if not start_path.exists() or not start_path.is_dir():
        return f"Error: Directory {directory} does not exist."
        
    tree_lines = [f"📁 {start_path.name}/"]
    
    def add_nodes(path: Path, prefix: str, current_depth: int):
        if current_depth > max_depth:
            return
            
        try:
            # Trier les dossiers en premier, puis les fichiers alphabétiquement
            paths = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            # Filtrer les dossiers ignorés et les fichiers cachés inintéressants
            paths = [p for p in paths if p.name not in ignore_dirs and not p.name.startswith("._")]
            
            pointers = [("├── " if i < len(paths) - 1 else "└── ") for i in range(len(paths))]
            
            for pointer, p in zip(pointers, paths):
                if p.is_dir():
                    tree_lines.append(f"{prefix}{pointer}📁 {p.name}/")
                    extension = "│   " if pointer == "├── " else "    "
                    add_nodes(p, prefix + extension, current_depth + 1)
                else:
                    tree_lines.append(f"{prefix}{pointer}📄 {p.name}")
        except PermissionError:
            tree_lines.append(f"{prefix}└── 🔒 [Access Denied]")
            
    add_nodes(start_path, "", 1)
    
    return "\n".join(tree_lines)

schema = {
    "name": "generate_context_map",
    "description": "Builds a visual, structural tree map of a project directory. Automatically ignores common noise directories like .git or node_modules. Essential for understanding codebase architecture.",
    "parameters": {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "The root directory to map (default is current directory '.')."
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum depth of folders to traverse (default 3)."
            }
        }
    }
}
