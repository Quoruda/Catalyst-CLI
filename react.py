import re
from typing import Dict, Any, List, Optional, Callable
from agent import CatalystAgent
from tools import available_tools, tools_description

class ReActAgent:
    def __init__(self, agent: CatalystAgent):
        self.agent = agent
        self.system_prompt = f"""You are Catalyst, an agent that operates in a loop of Thought, Action, and Observation.
You have access to the following tools:

{tools_description}

Format for calling a tool:
Action: tool_name[arguments]

After the tool runs, you will receive:
Observation: result of the tool

When you have the final answer to the user, format it as:
Final Answer: your detailed response

Example session:
Thought: I need to check who is the current user.
Action: execute_bash[whoami]
Observation: STDOUT: audrick
Thought: I know the user is audrick.
Final Answer: The current user is audrick.

Begin!"""

    def run(self, query: str, step_callback: Optional[Callable[[str, str, str], None]] = None) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query}
        ]
        
        max_steps = 10
        for _ in range(max_steps):
            response = self.agent.generate(messages)
            
            action_match = re.search(r"Action:\s*(\w+)\[([\s\S]*?)\]", response)
            
            if action_match:
                tool_name = action_match.group(1)
                tool_args = action_match.group(2).strip()
                
                thought = ""
                thought_match = re.search(r"Thought:\s*(.*?)(?=Action:|$)", response, re.DOTALL)
                if thought_match:
                    thought = thought_match.group(1).strip()
                
                if tool_name in available_tools:
                    if step_callback:
                        step_callback("thought", thought, "")
                        step_callback("action", tool_name, tool_args)
                        
                    observation = available_tools[tool_name](tool_args)
                    
                    if step_callback:
                        step_callback("observation", tool_name, observation)
                        
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "user", "content": f"Observation: {observation}"})
                else:
                    error_msg = f"Tool '{tool_name}' not found."
                    if step_callback:
                        step_callback("error", tool_name, error_msg)
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "user", "content": f"Observation: {error_msg}"})
            else:
                final_match = re.search(r"Final Answer:\s*([\s\S]*)", response)
                if final_match:
                    return final_match.group(1).strip()
                return response
                
        return "Failed to complete task within step limit."
