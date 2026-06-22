from providers import LiteLLMProvider
from config import AgentConfig, active_config

def ask_llm(system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
    """
    Magic function: A base utility to easily use the configured LLM inside any standard Python tool.
    This allows creating smart, AI-powered tools without the complexity and overhead of spawning a full agent.
    """
    config = active_config.model_copy(update={"temperature": temperature})
    
    llm = LiteLLMProvider(config)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        response = llm.generate(messages)
        return response.content
    except Exception as e:
        return f"Magic function LLM error: {str(e)}"
