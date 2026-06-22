from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import litellm
from litellm import completion
from models import AgentConfig

litellm.telemetry = False

class LLMResponse:
    def __init__(self, content: Optional[str] = None, tool_calls: Optional[List[Dict[str, Any]]] = None, reasoning: Optional[str] = None, usage: Optional[Dict[str, int]] = None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.reasoning = reasoning
        self.usage = usage or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

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
        
        provider = config.provider.lower() if config.provider else ""
        self.provider = provider
        if provider and "/" not in config.model:
            self.model = f"{provider}/{config.model}"
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
        if self.provider:
            kwargs["custom_llm_provider"] = self.provider
        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.api_key:
            kwargs["api_key"] = self.api_key
            
        if response_format:
            kwargs["response_format"] = response_format
            
        if tools:
            kwargs["tools"] = [{"type": "function", "function": t} for t in tools]
            
        kwargs["num_retries"] = 3
            
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
            
        usage_dict = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if hasattr(response, "usage") and response.usage:
            usage_dict["prompt_tokens"] = getattr(response.usage, "prompt_tokens", 0)
            usage_dict["completion_tokens"] = getattr(response.usage, "completion_tokens", 0)
            usage_dict["total_tokens"] = getattr(response.usage, "total_tokens", 0)
            
            cost = 0.0
            try:
                import litellm
                cost = litellm.completion_cost(completion_response=response)
            except Exception:
                pass
            from metrics import global_metrics
            global_metrics.add(usage_dict["prompt_tokens"], usage_dict["completion_tokens"], cost)
            
        return LLMResponse(content=message.content, tool_calls=tool_calls, reasoning=reasoning, usage=usage_dict)
