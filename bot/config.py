import os
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List, Optional, Set

load_dotenv()

class Settings(BaseSettings):
    # Telegram Bot settings
    BOT_TOKEN: str
    ALLOWED_USER_IDS_STR: Optional[str] = Field(None, env='ALLOWED_USER_IDS')

    # Supabase settings
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # AI settings
    DASHSCOPE_API_KEY: Optional[str] = None
    AI_API_KEY: Optional[str] = None  # OpenRouter API key

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
            print(f"ОШИБКА: Не удалось обработать ALLOWED_USER_IDS: '{self.ALLOWED_USER_IDS_STR}'. {str(e)}")
            return set()

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'


app_settings = Settings()