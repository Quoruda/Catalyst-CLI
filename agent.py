import os
from typing import Dict, Any, List, Optional, Callable
from dotenv import load_dotenv
from config import AgentConfig
from providers import LLMProvider, LiteLLMProvider, LLMResponse

class CatalystAgent:
    def __init__(self, env_path: Optional[str] = None):
        if env_path:
            load_dotenv(dotenv_path=env_path)
        else:
            load_dotenv()
            
        self.config = AgentConfig(
            provider=os.getenv("LLM_PROVIDER", "ollama").lower(),
            model=os.getenv("LLM_MODEL", "mistral:latest"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
            api_base=os.getenv("LLM_API_BASE"),
            api_key=os.getenv("LLM_API_KEY")
        )
        
        self.provider = self._init_provider()

    def _init_provider(self) -> LLMProvider:
        return LiteLLMProvider(self.config)

    def generate(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        try:
            return self.provider.generate(messages, tools, response_format)
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {str(e)}") from e

class BaseAgent:
    def __init__(self, name: str, description: str, engine: str = "Python", tools: List[str] = None, delegates: List[str] = None, delegation_instruction: str = ""):
        self.name = name
        self.description = description
        self.engine = engine
        self.tools = tools or []
        self.delegates = delegates or []
        self.delegation_instruction = delegation_instruction
        self._step_callback = None
        self._catalyst_agent = None

    @property
    def catalyst_agent(self):
        if self._catalyst_agent is None:
            self._catalyst_agent = CatalystAgent()
        return self._catalyst_agent

    def generate(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None, response_format: Optional[Dict[str, Any]] = None) -> LLMResponse:
        return self.catalyst_agent.generate(messages, tools, response_format)

    def call_tool(self, name: str, **kwargs) -> Any:
        from tools import available_tools
        if name not in available_tools:
            err = f"Tool '{name}' not found."
            self.log_error(err)
            return err
            
        import json
        self.log_action(name, json.dumps(kwargs))
        try:
            result = available_tools[name](**kwargs)
            self.log_observation(name, str(result))
            return result
        except Exception as e:
            err = f"Error: {str(e)}"
            self.log_error(err)
            return err

    def log_thought(self, content: str):
        if self._step_callback:
            self._step_callback("thought", "start", "")
            self._step_callback("thought", "done", content)

    def log_action(self, name: str, detail: str):
        if self._step_callback:
            self._step_callback("action", name, detail)

    def log_observation(self, name: str, detail: str):
        if self._step_callback:
            self._step_callback("observation", name, detail)

    def log_error(self, message: str):
        if self._step_callback:
            self._step_callback("error", "", message)

    def run(self, query: str, history: List[Dict[str, str]], step_callback: Optional[Callable[[str, str, str], None]] = None) -> str:
        raise NotImplementedError("Subclasses must implement run()")
