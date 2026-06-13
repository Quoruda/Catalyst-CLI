from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from openai import OpenAI
import requests
from config import AgentConfig

class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        pass

class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, config: AgentConfig):
        self.model = config.model
        self.temperature = config.temperature
        self.client = OpenAI(
            base_url=config.api_base,
            api_key=config.api_key or "ollama"
        )

    def generate(
        self, 
        messages: List[Dict[str, str]], 
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

class GeminiProvider(LLMProvider):
    def __init__(self, config: AgentConfig):
        self.model = config.model
        self.temperature = config.temperature
        self.api_key = config.api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def generate(
        self, 
        messages: List[Dict[str, str]], 
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key is required.")
            
        contents = []
        system_instruction = None
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            else:
                gemini_role = "user" if role == "user" else "model"
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })
                
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        generation_config = {
            "temperature": self.temperature
        }
        
        if response_format and response_format.get("type") == "json_object":
            generation_config["responseMimeType"] = "application/json"
            if "schema" in response_format:
                generation_config["responseSchema"] = response_format["schema"]
                
        payload = {
            "contents": contents,
            "generationConfig": generation_config
        }
        
        if system_instruction:
            payload["systemInstruction"] = system_instruction
            
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected response structure from Gemini API: {data}") from e
