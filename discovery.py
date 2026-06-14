import os
import sys
import importlib.util

class Agent:
    def __init__(self, name: str, description: str, engine: str, tools: list[str], system_prompt: str):
        self.name = name
        self.description = description
        self.engine = engine
        self.tools = tools
        self.system_prompt = system_prompt

    def __repr__(self):
        return f"<Agent name={self.name} engine={self.engine}>"

available_tools = {}
tools_schema = []

available_agents = {}

def get_resolution_paths(subdir_name: str) -> list[tuple[str, str]]:
    project_root = os.path.dirname(os.path.abspath(__file__))
    user_home = os.path.expanduser("~/.catalyst")
    cwd_local = os.path.abspath(".catalyst")
    
    paths = [
        (os.path.join(project_root, subdir_name), f"default_{subdir_name}"),
        (os.path.join(user_home, subdir_name), f"user_{subdir_name}"),
        (os.path.join(cwd_local, subdir_name), f"local_{subdir_name}"),
    ]
    return paths

def load_tools():
    available_tools.clear()
    del tools_schema[:]
    
    paths = get_resolution_paths("tools")
    
    for directory, package_name in paths:
        if not os.path.exists(directory):
            continue
            
        for filename in os.listdir(directory):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                full_module_name = f"{package_name}.{module_name}"
                filepath = os.path.join(directory, filename)
                
                spec = importlib.util.spec_from_file_location(full_module_name, filepath)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[full_module_name] = module
                    try:
                        spec.loader.exec_module(module)
                        if hasattr(module, "schema"):
                            schema = getattr(module, "schema")
                            name = schema.get("name")
                            func = getattr(module, name, None)
                            if func:
                                if name in available_tools:
                                    raise ValueError(f"Duplicate tool registration detected: '{name}' in '{filepath}'")
                                available_tools[name] = func
                                tools_schema.append(schema)
                    except Exception as e:
                        if isinstance(e, ValueError):
                            raise e

def parse_agent_markdown(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    metadata = {}
    system_prompt = ""
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            front_matter = parts[1]
            system_prompt = parts[2].strip()
            
            current_key = None
            for line in front_matter.split("\n"):
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                
                if line_stripped.startswith("- ") and current_key:
                    item_value = line_stripped[2:].strip()
                    if current_key not in metadata:
                        metadata[current_key] = []
                    elif not isinstance(metadata[current_key], list):
                        metadata[current_key] = [metadata[current_key]]
                    metadata[current_key].append(item_value)
                elif ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    current_key = key
                    
                    if value:
                        if value.startswith("[") and value.endswith("]"):
                            items = [item.strip() for item in value[1:-1].split(",") if item.strip()]
                            metadata[key] = items
                        else:
                            metadata[key] = value
                    else:
                        metadata[key] = []
        else:
            system_prompt = content.strip()
    else:
        system_prompt = content.strip()
        
    metadata["system_prompt"] = system_prompt
    return metadata

def load_agents():
    available_agents.clear()
    paths = get_resolution_paths("agents")
    
    for directory, package_name in paths:
        if not os.path.exists(directory):
            continue
            
        for filename in os.listdir(directory):
            if filename.endswith(".md"):
                filepath = os.path.join(directory, filename)
                try:
                    agent_config = parse_agent_markdown(filepath)
                    name = agent_config.get("name")
                    if not name:
                        name = os.path.splitext(filename)[0]
                        
                    if name in available_agents:
                        raise ValueError(f"Duplicate agent registration detected: '{name}' in '{filepath}'")
                        
                    agent_obj = Agent(
                        name=name,
                        description=agent_config.get("description", "No description provided."),
                        engine=agent_config.get("engine", "ReAct"),
                        tools=agent_config.get("tools", []),
                        system_prompt=agent_config.get("system_prompt", "")
                    )
                    available_agents[name] = agent_obj
                except Exception as e:
                    if isinstance(e, ValueError):
                        raise e

load_tools()
load_agents()
