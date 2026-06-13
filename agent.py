import os
from typing import Dict, Any, List, Optional
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
