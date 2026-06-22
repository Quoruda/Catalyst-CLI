import os
from models import AgentConfig

# Global in-memory configuration, initialized with environment variables as a fallback
active_config = AgentConfig(
    provider=os.getenv("LLM_PROVIDER", "ollama").lower(),
    model=os.getenv("LLM_MODEL", "mistral:latest"),
    temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
    api_base=os.getenv("LLM_API_BASE") or None,
    api_key=os.getenv("LLM_API_KEY") or None
)

