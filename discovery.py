import os
import sys
import importlib.util
import contextvars

class Agent:
    def __init__(self, name: str, description: str, engine: str, tools: list[str], system_prompt: str, delegates: list[str] = None, delegation_instruction: str = ""):
        self.name = name
        self.description = description
        self.engine = engine
        self.tools = tools
        self.system_prompt = system_prompt
        self.delegates = delegates or []
        self.delegation_instruction = delegation_instruction

    def __repr__(self):
        return f"<Agent name={self.name} engine={self.engine}>"

nesting_level = contextvars.ContextVar("nesting_level", default=0)
current_step_callback = contextvars.ContextVar("current_step_callback", default=None)
active_agent_name = contextvars.ContextVar("active_agent_name", default="catalyst")

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
                            if name.startswith("delegate_to_") or name.startswith("deleguate_to_"):
                                raise ValueError(f"Custom tools are not allowed to start with 'delegate_to_' or 'deleguate_to_': '{name}' in '{filepath}'")
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
            filepath = os.path.join(directory, filename)
            if filename.endswith(".md"):
                try:
                    agent_config = parse_agent_markdown(filepath)
                    name = agent_config.get("name")
                    if not name:
                        name = os.path.splitext(filename)[0]
                        
                    import re
                    if not re.match(r"^[a-zA-Z0-9_]+$", name):
                        raise ValueError(f"Agent name '{name}' in '{filepath}' contains invalid characters. Only alphanumeric characters and underscores are allowed.")
                        
                    if name in available_agents:
                        raise ValueError(f"Duplicate agent registration detected: '{name}' in '{filepath}'")
                        
                    delegates_val = agent_config.get("delegates", [])
                    if isinstance(delegates_val, str):
                        delegates_list = [delegates_val] if delegates_val else []
                    else:
                        delegates_list = list(delegates_val) if delegates_val is not None else []
                        
                    agent_obj = Agent(
                        name=name,
                        description=agent_config.get("description", "No description provided."),
                        engine=agent_config.get("engine", "ReAct"),
                        tools=agent_config.get("tools", []),
                        system_prompt=agent_config.get("system_prompt", ""),
                        delegates=delegates_list,
                        delegation_instruction=agent_config.get("delegation_instruction", "")
                    )
                    available_agents[name] = agent_obj
                except Exception as e:
                    if isinstance(e, ValueError):
                        raise e

def generate_delegation_tools():
    for agent_name, agent_obj in list(available_agents.items()):
        tool_name = f"delegate_to_{agent_name}"
        if tool_name in available_tools:
            continue
            
        def make_delegate_func(name=agent_name):
            def delegate_func(query: str) -> str:
                from agent import CatalystAgent
                from react import ReActAgent
                
                level_token = nesting_level.set(nesting_level.get() + 1)
                try:
                    agent_wrapper = CatalystAgent()
                    target_agent = ReActAgent(agent_wrapper, agent_name=name)
                    parent_callback = current_step_callback.get()
                    response = target_agent.run(query, history=[], step_callback=parent_callback)
                    return response
                finally:
                    nesting_level.reset(level_token)
            return delegate_func
            
        available_tools[tool_name] = make_delegate_func()
        
        desc = f"Delegates a complex sub-task to the specialized agent '{agent_name}'. Description: {agent_obj.description}"
        if agent_obj.delegation_instruction:
            desc += f" Instructions for formulating the query: {agent_obj.delegation_instruction}"
            
        schema = {
            "name": tool_name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A highly detailed, self-contained instruction for the delegated agent. Specify exactly what information you need, include all relevant context, URLs, or previous findings so the agent does not lack context. Do not be lazy or vague."
                    }
                },
                "required": ["query"]
            }
        }
        tools_schema.append(schema)

load_tools()
load_agents()
generate_delegation_tools()
