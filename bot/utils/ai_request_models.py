# models/ai_request_models.py
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class AIRequestEntities(BaseModel):
    employee_name: Optional[str] = None
    department: Optional[str] = None
    project: Optional[str] = None
    date: Optional[str] = None
    event_type: Optional[str] = None
    task_keyword: Optional[str] = None
    location: Optional[str] = None

    class Config:
        extra = 'allow'

class AIRequest(BaseModel):
    intent: str # Можно заменить на Enum Intent
    entities: Optional[AIRequestEntities] = Field(default_factory=dict)