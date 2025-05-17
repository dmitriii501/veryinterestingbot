<<<<<<< Updated upstream
import os
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    bot_token: str = Field(..., env='BOT_TOKEN')

    allowed_user_ids_str: str = Field("", env='ALLOWED_USER_IDS')

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
=======
# config/settings.py

from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., env='BOT_TOKEN')
    OPENAPI_API_KEY: str = Field(..., env='GROQ_API_KEY')  # ✅ Добавлено

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
>>>>>>> Stashed changes
