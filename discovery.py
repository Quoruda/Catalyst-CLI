import os
import sys
import importlib.util
import contextvars

class Skill:
    def __init__(self, name: str, description: str, tools: list[str], directives: str, temperature: float = None):
        self.name = name
        self.description = description
        self.tools = tools
        self.directives = directives
        self.temperature = temperature

    def __repr__(self):
        return f"<Skill name={self.name} tools={self.tools}>"

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

available_skills = {}
available_agents = {}
available_engines = {}
engine_descriptions = {}

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
                        schemas_to_register = []
                        if hasattr(module, "schemas"):
                            schemas_to_register.extend(getattr(module, "schemas"))
                        elif hasattr(module, "schema"):
                            schemas_to_register.append(getattr(module, "schema"))
                            
                        for schema in schemas_to_register:
                            name = schema.get("name")
                            if name.startswith("delegate_to_") or name.startswith("deleguate_to_"):
                                raise ValueError(f"Custom tools are not allowed to start with 'delegate_to_' or 'deleguate_to_': '{name}' in '{filepath}'")
                            func = getattr(module, name, None)
                            if func:
                                if name in available_tools:
                                    raise ValueError(f"Duplicate tool registration detected: '{name}' in '{filepath}'")
                                
                                # Enforce strict properties (no parameter hallucinations allowed)
                                if "parameters" in schema and isinstance(schema["parameters"], dict):
                                    schema["parameters"]["additionalProperties"] = False
                                    
                                available_tools[name] = func
                                tools_schema.append(schema)
                    except Exception as e:
                        if isinstance(e, ValueError):
                            raise e

def load_engines():
    available_engines.clear()
    engine_descriptions.clear()
    paths = get_resolution_paths("engines")
    
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
                        engine_class = getattr(module, "Engine", None)
                        if engine_class:
                            engine_name = getattr(module, "ENGINE_NAME", module_name)
                            engine_desc = getattr(module, "ENGINE_DESCRIPTION", "")
                            available_engines[engine_name.lower()] = engine_class
                            engine_descriptions[engine_name.lower()] = engine_desc
                    except Exception:
                        pass

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
                        
                    temp_config = Agent(
                        name=name,
                        description=agent_config.get("description", "No description provided."),
                        engine=agent_config.get("engine", "ReAct"),
                        tools=agent_config.get("tools", []),
                        system_prompt=agent_config.get("system_prompt", ""),
                        delegates=delegates_list,
                        delegation_instruction=agent_config.get("delegation_instruction", "")
                    )
                    engine_key = temp_config.engine.lower()
                    if engine_key in available_engines:
                        engine_class = available_engines[engine_key]
                        agent_obj = engine_class(temp_config)
                    else:
                        raise ValueError(f"Engine '{temp_config.engine}' for agent '{temp_config.name}' is not registered.")
                    available_agents[name] = agent_obj
                except Exception as e:
                    if isinstance(e, ValueError):
                        raise e
            elif filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                full_module_name = f"{package_name}.{module_name}"
                spec = importlib.util.spec_from_file_location(full_module_name, filepath)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[full_module_name] = module
                    try:
                        spec.loader.exec_module(module)
                        from agent import BaseAgent
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if isinstance(attr, type) and issubclass(attr, BaseAgent) and attr is not BaseAgent:
                                agent_instance = attr()
                                available_agents[agent_instance.name] = agent_instance
                    except Exception:
                        pass

def generate_delegation_tools():
    for agent_name, agent_obj in available_agents.items():
        if agent_name in ["metamorph", "catalyst"]:
            continue
        
        tool_name = f"delegate_to_{agent_name}"
        if tool_name in available_tools:
            continue
            
        def make_delegate_func(name=agent_name):
            def delegate_func(query: str, **kwargs) -> str:
                level_token = nesting_level.set(nesting_level.get() + 1)
                try:
                    target_agent = available_agents[name]
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
                "required": ["query"],
                "additionalProperties": False
            }
        }
        tools_schema.append(schema)

def load_skills():
    available_skills.clear()
    paths = get_resolution_paths("skills")
    
    for directory, _ in paths:
        if not os.path.exists(directory):
            continue
            
        for filename in os.listdir(directory):
            if not filename.endswith(".md"):
                continue
            filepath = os.path.join(directory, filename)
            try:
                config = parse_agent_markdown(filepath)
                name = config.get("name")
                if not name:
                    name = os.path.splitext(filename)[0]
                    
                if name in available_skills:
                    raise ValueError(f"Duplicate skill registration detected: '{name}' in '{filepath}'")
                    
                tools_list = config.get("tools", [])
                if isinstance(tools_list, str):
                    tools_list = [tools_list] if tools_list else []
                    
                skill = Skill(
                    name=name,
                    description=config.get("description", "No description provided."),
                    tools=tools_list,
                    directives=config.get("system_prompt", ""),
                    temperature=config.get("temperature")
                )
                available_skills[name] = skill
            except Exception as e:
                if isinstance(e, ValueError):
                    raise e

def resolve_skills(skill_names: list[str]) -> tuple[list[str], str, float]:
    """Resolve a list of skill names into a flat list of tool names, combined directives text, and max temperature."""
    resolved_tools = []
    directives_parts = []
    seen_tools = set()
    max_temp = None
    
    for skill_name in skill_names:
        skill = available_skills.get(skill_name)
        if not skill:
            continue
        for tool_name in skill.tools:
            if tool_name not in seen_tools:
                resolved_tools.append(tool_name)
                seen_tools.add(tool_name)
        if skill.directives:
            directives_parts.append(f"## Skill: {skill.name}\n{skill.directives}")
        if skill.temperature is not None:
            if max_temp is None or skill.temperature > max_temp:
                max_temp = float(skill.temperature)
            
    combined_directives = "\n\n".join(directives_parts)
    return resolved_tools, combined_directives, max_temp

load_tools()
load_engines()
load_skills()
load_agents()
generate_delegation_tools()
