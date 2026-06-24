import json
from typing import Dict, Any, List, Optional, Callable
from agent import BaseAgent


class SupervisorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="supervisor",
            description="Adaptive agent that dynamically selects skills and engine based on each user request.",
            delegation_instruction="Provide a clear task description. The supervisor agent will autonomously select the appropriate skills and tools."
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

    def route(self, query: str, history: List[Dict[str, str]] = None) -> dict:
        """CALL 1 — Lightweight LLM router to classify intent and select engine + skills."""
        from discovery import available_skills, available_engines, engine_descriptions
        from magic import ask_llm

        skills_block = "\n".join(
            f"- {name}: {skill.description}" for name, skill in available_skills.items()
        )
        engines_block = "\n".join(
            f"- {name}: {desc}" for name, desc in engine_descriptions.items()
        )

        history_context = ""
        if history:
            history_context = "Recent conversation context:\n"
            for msg in history[-20:]: # Include up to 20 messages for deep context
                role = msg.get("role", "unknown")
                if role == "system":
                    continue
                content = msg.get("content", "")
                history_context += f"{role}: {content}\n"

        system_prompt = (
            "You are a routing classifier. Your sole job is to analyze the user's request "
            "and select the most appropriate engine and skills from the lists below.\n"
            "Select between 1 and 4 skills maximum. Choose the single best engine.\n\n"
            f"Available engines:\n{engines_block}\n\n"
            f"Available skills:\n{skills_block}\n\n"
            f"{history_context}\n"
            "Respond ONLY with a JSON object: {\"engine\": \"engine_name\", \"skills\": [\"skill1\", \"skill2\"]}"
        )

        try:
            raw = ask_llm(
                system_prompt=system_prompt,
                user_prompt=query,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            raw = raw.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            elif raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError, ValueError):
            return {"engine": "react", "skills": list(available_skills.keys())}

        # Validate engine against registry
        engine = data.get("engine", "react")
        if engine.lower() not in available_engines:
            engine = "react"

        # Validate skills against registry, drop unknowns
        skills = [s for s in data.get("skills", []) if s in available_skills]
        if not skills:
            skills = list(available_skills.keys())

        return {"engine": engine.lower(), "skills": skills}

    def run(self, query: str, history: List[Dict[str, str]], step_callback: Optional[Callable[[str, str, str], None]] = None) -> str:
        self._step_callback = step_callback
        from discovery import available_engines, active_agent_name, Agent

        token_agent = active_agent_name.set(self.name)
        try:
            if step_callback:
                step_callback("agent_start", self.name, query)

            # === CALL 1: Route ===
            self.log_thought("Routing request to select engine and skills...")
            decision = self.route(query, history=history)
            engine_name = decision["engine"]
            skill_names = decision["skills"]

            self.log_thought(f"Router decision → engine={engine_name}, skills={skill_names}")

            # Load the selected skills to resolve tools and directives
            self.load_skills(skill_names)

            # === CALL 2: Build and run the real agent with a fresh context ===
            engine_class = available_engines.get(engine_name)
            if not engine_class:
                engine_class = available_engines.get("react")

            # Fabricate a temporary agent config with the resolved context
            agent_config = Agent(
                name="worker",
                description="Dynamic worker spawned by the supervisor agent.",
                engine=engine_name,
                tools=self._active_tool_names,
                system_prompt=self._active_directives,
                delegates=[],
                delegation_instruction=""
            )

            worker = engine_class(agent_config)
            result = worker.run(query, history=history, step_callback=step_callback)

            if step_callback:
                step_callback("agent_done", self.name, "")

            return result

        except Exception as e:
            self.log_error(f"Supervisor failed: {e}")
            if step_callback:
                step_callback("agent_done", self.name, "")
            return f"Supervisor failed: {e}"
        finally:
            active_agent_name.reset(token_agent)
