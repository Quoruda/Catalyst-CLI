from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import litellm
from litellm import completion
from config import AgentConfig

litellm.telemetry = False

class LLMResponse:
    def __init__(self, content: Optional[str] = None, tool_calls: Optional[List[Dict[str, Any]]] = None, reasoning: Optional[str] = None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.reasoning = reasoning

class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        pass

class LiteLLMProvider(LLMProvider):
    def __init__(self, config: AgentConfig):
        self.temperature = config.temperature
        self.api_base = config.api_base
        self.api_key = config.api_key
        
        provider = config.provider.lower()
        if provider == "gemini":
            if not config.model.startswith("gemini/"):
                self.model = f"gemini/{config.model}"
            else:
                self.model = config.model
        elif provider == "ollama":
            if not config.model.startswith("ollama/"):
                self.model = f"ollama/{config.model}"
            else:
                self.model = config.model
        else:
            self.model = config.model

    def generate(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.api_key:
            kwargs["api_key"] = self.api_key
            
        if response_format:
            kwargs["response_format"] = response_format
            
        if tools:
            kwargs["tools"] = [{"type": "function", "function": t} for t in tools]
            
        response = completion(**kwargs)
        message = response.choices[0].message
        
        tool_calls = []
        if getattr(message, "tool_calls", None):
            for tc in message.tool_calls:
                args = tc.function.arguments
                if not isinstance(args, str):
                    args = json.dumps(args)
                tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": args
                    }
                })
                
        reasoning = getattr(message, "reasoning_content", None)
        if not reasoning and isinstance(message, dict):
            reasoning = message.get("reasoning_content")
        if reasoning and not isinstance(reasoning, str):
            reasoning = str(reasoning)
            
        return LLMResponse(content=message.content, tool_calls=tool_calls, reasoning=reasoning)
