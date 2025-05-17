# config/settings.py

from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., env='BOT_TOKEN')
    OPENAPI_API_KEY: str = Field(...)  # для Groq/Llama3
  
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()