import os
import sys
import importlib.util

available_tools = {}
tools_schema = []

def load_tools_from_dir(directory: str, package_name: str = ""):
    if not os.path.exists(directory):
        return
        
    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            full_module_name = f"{package_name}.{module_name}" if package_name else module_name
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

tools_dir = os.path.dirname(__file__)
load_tools_from_dir(tools_dir, "tools")

custom_dir = os.path.join(os.path.dirname(tools_dir), "custom_tools")
if not os.path.exists(custom_dir):
    os.makedirs(custom_dir)
load_tools_from_dir(custom_dir, "custom_tools")
