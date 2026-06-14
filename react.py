import json
from typing import Dict, Any, List, Optional, Callable
from agent import CatalystAgent

class ReActAgent:
    def __init__(self, agent: CatalystAgent, agent_name: str = "catalyst"):
        self.agent = agent
        self.agent_name = agent_name
        
        from discovery import available_agents
        self.config = available_agents.get(agent_name)
        if not self.config:
            raise ValueError(f"Agent '{agent_name}' not found in registered agents.")
            
        self.system_prompt = self.config.system_prompt
        
        from tools import tools_schema
        allowed_tools = self.config.tools
        self.agent_tools_schema = [
            schema for schema in tools_schema if schema["name"] in allowed_tools
        ]

    def run(self, query: str, history: List[Dict[str, str]], step_callback: Optional[Callable[[str, str, str], None]] = None) -> str:
        if not history:
            history.append({"role": "system", "content": self.system_prompt})
            
        history.append({"role": "user", "content": query})
        messages = list(history)
        
        from tools import available_tools
        max_steps = 10
        for _ in range(max_steps):
            if step_callback:
                step_callback("thought", "start", "")
            response = self.agent.generate(messages, tools=self.agent_tools_schema)
            
            if step_callback:
                step_callback("thought", "done", response.reasoning or "")
                
            if response.tool_calls:
                assistant_msg = {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": response.tool_calls
                }
                messages.append(assistant_msg)
                    
                for tc in response.tool_calls:
                    tool_name = tc["function"]["name"]
                    tool_args_raw = tc["function"]["arguments"]
                    
                    if isinstance(tool_args_raw, str):
                        try:
                            tool_args = json.loads(tool_args_raw)
                        except Exception:
                            tool_args = {"command": tool_args_raw}
                    else:
                        tool_args = tool_args_raw
                        
                    args_str = json.dumps(tool_args)
                    if step_callback:
                        step_callback("action", tool_name, args_str)
                        
                    if tool_name in available_tools:
                        try:
                            if isinstance(tool_args, dict):
                                observation = available_tools[tool_name](**tool_args)
                            else:
                                observation = available_tools[tool_name](tool_args)
                        except Exception as e:
                            observation = f"Error executing tool: {str(e)}"
                    else:
                        observation = f"Tool '{tool_name}' not found."
                        
                    if step_callback:
                        step_callback("observation", tool_name, observation)
                        
                    tool_response_msg = {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": tool_name,
                        "content": observation
                    }
                    messages.append(tool_response_msg)
            else:
                final_answer = response.content or ""
                history.append({"role": "assistant", "content": final_answer})
                return final_answer
                
        error_res = "Failed to complete task within step limit."
        history.append({"role": "assistant", "content": error_res})
        return error_res
