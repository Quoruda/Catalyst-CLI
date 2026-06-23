from typing import Dict, Any, List, Optional, Callable
from agent import BaseAgent


class MetamorphAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="metamorph",
            description="Adaptive agent that dynamically selects skills and tools based on each user request. Empty shell for now.",
            delegation_instruction="Provide a clear task description. The metamorph agent will autonomously select the appropriate skills and tools."
        )
        self._active_skills = []
        self._active_tool_names = []
        self._active_directives = ""

    @property
    def active_skills(self) -> list:
        return list(self._active_skills)

    def get_available_skills(self) -> dict:
        from discovery import available_skills
        return dict(available_skills)

    def load_skills(self, skill_names: list[str]):
        from discovery import resolve_skills
        self._active_skills = list(skill_names)
        self._active_tool_names, self._active_directives = resolve_skills(skill_names)

    def get_active_tools_schema(self) -> list[dict]:
        from discovery import tools_schema
        return [s for s in tools_schema if s["name"] in self._active_tool_names]

    def run(self, query: str, history: List[Dict[str, str]], step_callback: Optional[Callable[[str, str, str], None]] = None) -> str:
        self._step_callback = step_callback
        from discovery import active_agent_name
        token_agent = active_agent_name.set(self.name)

        try:
            if step_callback:
                step_callback("agent_start", self.name, query)

            # TODO: Implement skill routing + LLM execution loop
            result = f"[Metamorph] Shell active. No LLM wired yet.\nAvailable skills: {list(self.get_available_skills().keys())}\nActive skills: {self._active_skills}\nActive tools: {self._active_tool_names}\nActive directives:\n{self._active_directives}"

            if step_callback:
                step_callback("agent_done", self.name, "")

            return result

        except Exception as e:
            self.log_error(f"Metamorph failed: {e}")
            if step_callback:
                step_callback("agent_done", self.name, "")
            return f"Metamorph failed: {e}"
        finally:
            active_agent_name.reset(token_agent)
