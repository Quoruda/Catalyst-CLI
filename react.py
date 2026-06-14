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
        allowed_tools = list(self.config.tools)
        for delegate_name in getattr(self.config, "delegates", []):
            allowed_tools.append(f"delegate_to_{delegate_name}")
            
        self.agent_tools_schema = []
        for schema in tools_schema:
            name = schema["name"]
            if name in allowed_tools:
                self.agent_tools_schema.append(schema)

    def run(self, query: str, history: List[Dict[str, str]], step_callback: Optional[Callable[[str, str, str], None]] = None) -> str:
        from discovery import current_step_callback, active_agent_name
        token_cb = current_step_callback.set(step_callback)
        token_agent = active_agent_name.set(self.agent_name)
        try:
            if step_callback:
                step_callback("agent_start", self.agent_name, query)
                
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
                    if step_callback:
                        step_callback("agent_done", self.agent_name, "")
                    return final_answer
                    
            error_res = "Failed to complete task within step limit."
            history.append({"role": "assistant", "content": error_res})
            if step_callback:
                step_callback("agent_done", self.agent_name, "")
            return error_res
        finally:
            current_step_callback.reset(token_cb)
            active_agent_name.reset(token_agent)
