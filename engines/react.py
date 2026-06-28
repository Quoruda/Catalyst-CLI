import json
import os
import datetime
import getpass
import platform
from typing import Dict, Any, List, Optional, Callable
from agent import BaseAgent

ENGINE_NAME = "ReAct"
ENGINE_DESCRIPTION = "Boucle conversationnelle Thought → Action → Observation. Idéal pour les tâches courtes, interactives, ou les questions-réponses nécessitant quelques appels d'outils."

class Engine(BaseAgent):
    def __init__(self, agent_config):
        super().__init__(
            name=agent_config.name,
            description=agent_config.description,
            engine=agent_config.engine,
            tools=agent_config.tools,
            delegates=agent_config.delegates,
            delegation_instruction=agent_config.delegation_instruction
        )
        self.system_prompt = agent_config.system_prompt

    @property
    def agent_tools_schema(self):
        from tools import tools_schema
        allowed_tools = list(self.tools)
        for delegate_name in self.delegates:
            allowed_tools.append(f"delegate_to_{delegate_name}")
            
        schema_list = []
        for schema in tools_schema:
            name = schema["name"]
            if name in allowed_tools:
                schema_list.append(schema)
        return schema_list

    def run(self, query: str, history: List[Dict[str, str]], step_callback: Optional[Callable[[str, str, str], None]] = None) -> str:
        self._step_callback = step_callback
        from discovery import current_step_callback, active_agent_name
        token_cb = current_step_callback.set(step_callback)
        token_agent = active_agent_name.set(self.name)
        try:
            if step_callback:
                step_callback("agent_start", self.name, query)
                
            live_context = f"\n\n---\n[LIVE SYSTEM CONTEXT]\nYou are running as a local AI agent on the user's machine. Here is the real-time context:\n- Current Date & Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n- Current Working Directory: {os.getcwd()}\n- Operating System: {platform.system()} {platform.release()}\n- The human user you are talking to is named: {getpass.getuser()}\n---"
            full_system_prompt = self.system_prompt + live_context
            
            if not history:
                history.append({"role": "system", "content": full_system_prompt})
            elif history[0].get("role") == "system":
                history[0]["content"] = full_system_prompt
            else:
                history.insert(0, {"role": "system", "content": full_system_prompt})
                
                
            history.append({"role": "user", "content": query})
            # Token economy disabled: we now store all tool calls and responses directly in the session history.
            messages = history
            
            max_steps = 25
            for _ in range(max_steps):
                self.log_thought("")
                response = self.generate(messages, tools=self.agent_tools_schema)
                
                if step_callback and response.reasoning:
                    step_callback("thought", "done", response.reasoning)
                    
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
                            
                        observation = self.call_tool(tool_name, **(tool_args if isinstance(tool_args, dict) else {"query": tool_args}))
                        
                        tool_response_msg = {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "name": tool_name,
                            "content": observation
                        }
                        messages.append(tool_response_msg)
                else:
                    final_answer = response.content or ""
                    if not final_answer and getattr(response, "reasoning", None):
                        final_answer = response.reasoning
                    history.append({"role": "assistant", "content": final_answer})
                    if step_callback:
                        step_callback("agent_done", self.name, "")
                    return final_answer
                    
            error_res = "Failed to complete task within step limit."
            history.append({"role": "assistant", "content": error_res})
            if step_callback:
                step_callback("agent_done", self.name, "")
            return error_res
        finally:
            current_step_callback.reset(token_cb)
            active_agent_name.reset(token_agent)
