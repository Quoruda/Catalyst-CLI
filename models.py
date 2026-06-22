from typing import Optional
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    provider: str
    model: str
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    api_base: Optional[str] = None
    api_key: Optional[str] = None
