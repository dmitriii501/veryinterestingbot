import os
from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings
from typing import List, Optional, Set
import logging
import logging.config

# Load environment variables
load_dotenv()

class LogConfig:
    """Logging configuration."""
    LOGGER_NAME: str = "corporate_bot"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_LEVEL: str = "INFO"

    # Logging config dict
    @classmethod
    def get_config(cls):
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": cls.LOG_FORMAT,
                }
            },
            "handlers": {
                "console": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "formatter": "default",
                    "class": "logging.FileHandler",
                    "filename": "bot.log",
                    "mode": "a",
                }
            },
            "loggers": {
                "": {  # root logger
                    "handlers": ["console", "file"],
                    "level": cls.LOG_LEVEL,
                }
            }
        }

class Settings(BaseSettings):
    # Telegram Bot settings
    BOT_TOKEN: SecretStr
    ALLOWED_USER_IDS_STR: Optional[str] = Field(None, env='ALLOWED_USER_IDS')

    # Supabase settings
    SUPABASE_URL: str
    SUPABASE_KEY: SecretStr

    # AI settings
    AI_API_KEY: SecretStr
    AI_BASE_URL: str = "https://inference.api.nscale.com/v1"
    AI_MODEL: str = "Qwen/Qwen3-235B-A22B"
    
    # NLU settings
    NLU_CONFIDENCE_THRESHOLD: float = 0.7
    
    # Response settings
    MAX_RESPONSE_LENGTH: int = 2000
    DEFAULT_RESPONSE_TIMEOUT: int = 30

    # Database settings
    DB_QUERY_TIMEOUT: int = 10
    MAX_QUERY_RESULTS: int = 50

    @property
    def ALLOWED_USER_IDS(self) -> Set[int]:
        """
        Преобразует строку с ID пользователей в множество целых чисел.
        Формат строки: "123456789, 987654321"
        """
        if not self.ALLOWED_USER_IDS_STR:
            return set()
        
        try:
            return {
                int(uid.strip())
                for uid in self.ALLOWED_USER_IDS_STR.split(',')
                if uid.strip().isdigit()
            }
        except ValueError as e:
            logging.error(f"ОШИБКА: Не удалось обработать ALLOWED_USER_IDS: '{self.ALLOWED_USER_IDS_STR}'. {str(e)}")
            return set()

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

# Create settings instance
app_settings = Settings()

# Configure logging
logging.config.dictConfig(LogConfig.get_config())