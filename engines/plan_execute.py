import json
import os
import datetime
import getpass
import platform
from typing import Dict, Any, List, Optional, Callable
from agent import BaseAgent

ENGINE_NAME = "PlanExecute"

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

    def generate_plan(self, query: str) -> List[str]:
        self.log_thought("Generating a step-by-step plan for the objective.")
        
        prompt = f"""You are the Planner module of a Plan & Execute agent. 
The user has provided the following objective:
"{query}"

Your task is to break down this objective into a logical, sequential list of discrete steps.
Make the steps clear and actionable.

Respond ONLY with a JSON array of strings, where each string is a step.
Example:
[
  "Step 1: Do X",
  "Step 2: Do Y",
  "Step 3: Verify Z"
]
"""
        try:
            res = self.generate([{"role": "user", "content": prompt}])
            content = res.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            plan = json.loads(content.strip())
            if isinstance(plan, list) and len(plan) > 0:
                return plan
        except Exception as e:
            self.log_error(f"Failed to parse initial plan: {str(e)}")
            
        return [query] # Fallback: the whole query is one step

    def replan(self, query: str, remaining_plan: List[str], current_step: str, step_result: str) -> List[str]:
        self.log_thought("Evaluating result and replanning if necessary...")
        
        prompt = f"""You are the Replanner module.
Original objective: "{query}"

We just completed this step: "{current_step}"
The result of this step was:
{step_result}

The remaining steps in our plan were:
{json.dumps(remaining_plan, indent=2)}

Based on the result of the completed step, do we need to modify the remaining plan? 
If the step failed or revealed new information that requires additional tasks (e.g. debugging, fixing an error), add those tasks to the plan.
If the step succeeded normally, simply return the remaining plan as is, or remove completed sub-tasks.
If the objective is completely achieved, return an empty array [].

Respond ONLY with a JSON array of strings representing the updated remaining steps.
"""
        try:
            res = self.generate([{"role": "user", "content": prompt}])
            content = res.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            plan = json.loads(content.strip())
            if isinstance(plan, list):
                return plan
        except Exception as e:
            self.log_error(f"Failed to parse updated plan: {str(e)}")
            
        return remaining_plan # Fallback

    def execute_step(self, step_query: str, query: str, execution_history: List[Dict[str, Any]]) -> str:
        self.log_thought(f"Executing step: {step_query}")
        
        live_context = f"\n\n---\n[LIVE SYSTEM CONTEXT]\nYou are running as a local AI agent on the user's machine.\n- Current Date & Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n- Current Working Directory: {os.getcwd()}\n---"
        
        full_system_prompt = self.system_prompt + live_context + f"\n\nYour overarching objective is: {query}\nYour IMMEDIATE task is strictly: {step_query}\nUse your tools to accomplish this immediate task. Once you have accomplished it, return a clear summary of what you did and the results."
        
        # Update system prompt for this step
        execution_history[0]["content"] = full_system_prompt
        
        # Add the immediate task as user prompt
        execution_history.append({"role": "user", "content": f"Please execute the following task: {step_query}"})
        
        max_react_steps = 7
        for _ in range(max_react_steps):
            response = self.generate(execution_history, tools=self.agent_tools_schema)
            
            if response.tool_calls:
                assistant_msg = {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": response.tool_calls
                }
                execution_history.append(assistant_msg)
                    
                for tc in response.tool_calls:
                    tool_name = tc["function"]["name"]
                    tool_args_raw = tc["function"]["arguments"]
                    
                    if isinstance(tool_args_raw, str):
                        try:
                            tool_args = json.loads(tool_args_raw)
                        except Exception:
                            tool_args = {"query": tool_args_raw}
                    else:
                        tool_args = tool_args_raw
                        
                    observation = self.call_tool(tool_name, **(tool_args if isinstance(tool_args, dict) else {"query": tool_args}))
                    
                    execution_history.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": tool_name,
                        "content": observation
                    })
            else:
                if response.content:
                    execution_history.append({"role": "assistant", "content": response.content})
                return response.content or "Completed without text output."
                
        return "Failed to complete step within internal tool limit."

    def run(self, query: str, history: List[Dict[str, str]], step_callback: Optional[Callable[[str, str, str], None]] = None) -> str:
        self._step_callback = step_callback
        from discovery import current_step_callback, active_agent_name
        token_cb = current_step_callback.set(step_callback)
        token_agent = active_agent_name.set(self.name)
        
        try:
            if step_callback:
                step_callback("agent_start", self.name, query)
                
            plan = self.generate_plan(query)
            self.log_thought(f"Initial Plan generated with {len(plan)} steps.")
            
            completed_steps_log = []
            
            # Initialize persistent execution history for the whole run
            live_context = f"\n\n---\n[LIVE SYSTEM CONTEXT]\nYou are running as a local AI agent on the user's machine.\n- Current Date & Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n- Current Working Directory: {os.getcwd()}\n---"
            execution_history = [
                {"role": "system", "content": self.system_prompt + live_context + f"\n\nYour overarching objective is: {query}"}
            ]
            
            max_plan_iterations = 20
            iterations = 0
            
            while plan and iterations < max_plan_iterations:
                iterations += 1
                current_step = plan.pop(0)
                
                self.log_action("Executing Plan Step", current_step)
                
                step_result = self.execute_step(current_step, query, execution_history)
                
                completed_steps_log.append(f"Task: {current_step}\nResult: {step_result}")
                
                if not plan:
                    self.log_thought("Plan queue is empty. Checking if completely done.")
                
                plan = self.replan(query, plan, current_step, step_result)
                
                if plan:
                    self.log_thought(f"Plan updated. {len(plan)} steps remaining.")
                else:
                    self.log_thought("Plan completed successfully.")
            
            if iterations >= max_plan_iterations:
                final_answer = "Stopped because the plan execution exceeded the maximum number of iterations."
            else:
                final_answer = "Objective accomplished. Summary of steps:\n\n" + "\n\n".join(completed_steps_log)
                
            history.append({"role": "assistant", "content": final_answer})
            
            if step_callback:
                step_callback("agent_done", self.name, "")
                
            return final_answer
            
        except Exception as e:
            err = f"PlanExecute Engine failed: {str(e)}"
            self.log_error(err)
            history.append({"role": "assistant", "content": err})
            if step_callback:
                step_callback("agent_done", self.name, "")
            return err
        finally:
            current_step_callback.reset(token_cb)
            active_agent_name.reset(token_agent)
