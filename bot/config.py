import os
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List, Optional

load_dotenv()

class Settings(BaseSettings):
    # Telegram Bot settings
    BOT_TOKEN: str
    ALLOWED_USER_IDS: Optional[List[int]] = None

    # Supabase settings
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # AI settings
    DASHSCOPE_API_KEY: Optional[str] = None

    @property
    def ALLOWED_USER_IDS(self) -> set[int]:
        ids_str = self.allowed_user_ids_str.strip()
        if not ids_str:
            return set()
        try:
            return {int(uid.strip()) for uid in ids_str.split(',') if uid.strip().isdigit()}
        except ValueError:
            print(
                f"ОШИБКА: Не удалось обработать ALLOWED_USER_IDS: '{ids_str}'. Убедитесь, что это список чисел, разделенных запятыми.")
            return set()

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

app_settings = Settings()