import os
import json
import logging
from typing import Dict, Any, Optional, Union
from bot.config import app_settings
from openai import OpenAI
from openai.types.chat import ChatCompletion
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class NLUProcessor:
    def __init__(self):
        self.api_key = app_settings.AI_API_KEY.get_secret_value()
        self.base_url = app_settings.AI_BASE_URL
        self.model = app_settings.AI_MODEL
        
        if not self.api_key:
            logger.error("AI_API_KEY not configured")
            raise ValueError("AI_API_KEY must be configured")

        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.info("Successfully initialized OpenAI client")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    def _get_system_prompt(self) -> str:
        """Returns the system prompt for NLU processing."""
        return (
            "Ты — AI-парсер запросов в корпоративном приложении. "
            "Пользователь пишет запрос в свободной форме. Твоя задача — извлечь только intent (намерение) "
            "и entities (сущности), которые явно указаны в тексте. Не отвечай на вопрос, не выдумывай данные, "
            "не интерпретируй неявные фразы. Дата должна быть только в формате дд.мм.гггг. "
            "Если дата указана иначе (например, 'завтра'), не добавляй сущность date. "
            "Если сущность не указана — не включай её в JSON.\n\n"
            "Возможные интенты:\n"
            "- find_employee: Поиск сотрудника или информации о сотруднике\n"
            "- find_by_position: Поиск сотрудников по должности\n"
            "- find_by_department: Поиск сотрудников по отделу\n"
            "- event_info: Инфо о мероприятиях\n"
            "- birthday_info: Дни рождения\n"
            "- task_info: Задачи\n"
            "- availability: Свободен ли сотрудник\n"
            "- lunch_game_invite: Найти коллег по интересам\n"
            "- general_question: Общий вопрос\n"
            "- unknown: Неопределено\n\n"
            "Возможные сущности:\n"
            "- employee_name: имя сотрудника\n"
            "- department: отдел\n"
            "- position: должность\n"
            "- info_type: тип запрашиваемой информации (education, hire_date, phone_number, job_title)\n"
            "- project: проект\n"
            "- date: дата (только в формате дд.мм.гггг)\n"
            "- event_type: тип события\n"
            "- task_keyword: ключ задачи\n"
            "- location: место"
        )

    def _validate_nlu_result(self, result: str) -> Optional[Dict[str, Any]]:
        """
        Validates and parses the NLU result.
        
        Args:
            result: String containing JSON response from AI
            
        Returns:
            Dict containing parsed and validated NLU result or None if invalid
        """
        try:
            # Remove any potential non-JSON content
            json_start = result.find('{')
            json_end = result.rfind('}')
            
            if json_start == -1 or json_end == -1:
                logger.error("No valid JSON object found in response")
                return None
                
            json_str = result[json_start:json_end + 1]
            data = json.loads(json_str)
            
            # Validate required fields
            if not isinstance(data, dict):
                logger.error("NLU result is not a dictionary")
                return None
                
            if "intent" not in data:
                logger.error("Missing 'intent' in NLU result")
                return None
                
            if not isinstance(data["intent"], str):
                logger.error("'intent' is not a string")
                return None
                
            # Validate entities if present
            if "entities" in data and not isinstance(data["entities"], dict):
                logger.error("'entities' is not a dictionary")
                return None
                
            # Validate intent values
            valid_intents = {
                "find_employee", "find_by_position", "find_by_department",
                "event_info", "birthday_info", "task_info", "availability",
                "lunch_game_invite", "general_question", "unknown"
            }
            
            if data["intent"] not in valid_intents:
                logger.error(f"Invalid intent value: {data['intent']}")
                return None
                
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse NLU result as JSON: {e}")
            logger.debug(f"Raw result: {result}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error validating NLU result: {e}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _call_ai_api(self, messages: list) -> Optional[ChatCompletion]:
        """
        Call the AI API with retry logic.
        """
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                temperature=0.1,  # Low temperature for more consistent results
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            return response
        except Exception as e:
            logger.error(f"Error calling AI API: {e}")
            raise

    async def process_query(self, user_query: str) -> Optional[Dict[str, Any]]:
        """
        Process a user query through the NLU pipeline.
        
        Args:
            user_query: The user's input text
            
        Returns:
            Dict containing intent and entities or None if processing failed
        """
        if not user_query.strip():
            logger.warning("Empty query received")
            return None

        try:
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": user_query},
            ]

            logger.debug(f"Sending request to AI model with query: {user_query}")
            
            response = await self._call_ai_api(messages)

            if not response or not response.choices or not response.choices[0].message:
                logger.warning("Empty or invalid response from AI model")
                return None

            result = response.choices[0].message.content.strip()
            logger.debug(f"Raw NLU result: {result}")

            validated_result = self._validate_nlu_result(result)
            if validated_result:
                logger.info(f"Successfully processed query. Intent: {validated_result['intent']}")
                return validated_result
            
            return None

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return None

# Create a global instance of NLUProcessor
_nlu_processor = None

def get_nlu_processor() -> NLUProcessor:
    """
    Get or create a global NLUProcessor instance.
    """
    global _nlu_processor
    if _nlu_processor is None:
        _nlu_processor = NLUProcessor()
    return _nlu_processor

async def process_user_query(user_query: str, system_prompt: str = None) -> Optional[Dict[str, Any]]:
    """
    Process a user query through the NLU pipeline.
    
    Args:
        user_query: The user's input text
        system_prompt: Optional custom system prompt
        
    Returns:
        Dict containing intent and entities or None if processing failed
    """
    try:
        if user_query is None:
            logger.error("Received None as user_query")
            return None
            
        processor = get_nlu_processor()
        return await processor.process_query(user_query)
    except Exception as e:
        logger.error(f"Error in process_user_query: {e}")
        return None

async def main():
    """
    Пример использования функции process_user_query.
    """
    user_query = "Найти сотрудников из отдела продаж 05.03.2024 и 06.03.2024"
    system_prompt = (
        "Ты — AI-парсер запросов в корпоративном приложении. "
        "Пользователь пишет запрос в свободной форме. Твоя задача — извлечь только intent (намерение) "
        "и entities (сущности), которые явно указаны в тексте. Не отвечай на вопрос, не выдумывай данные, "
        "не интерпретируй неявные фразы. Дата должна быть только в формате дд.мм.гггг. "
        "Если дата указана иначе (например, 'завтра'), не добавляй сущность date. "
        "Если сущность не указана — не включай её в JSON. "
        "Ответ строго в формате JSON.\n\n"
        "Возможные интенты:\n"
        "- find_employee: Поиск сотрудника\n"
        "- event_info: Инфо о мероприятиях\n"
        "- birthday_info: Дни рождения\n"
        "- task_info: Задачи\n"
        "- availability: Свободен ли сотрудник\n"
        "- lunch_game_invite: Найти коллег по интересам\n"
        "- general_question: Общий вопрос\n"
        "- unknown: Неопределено\n\n"
        "Возможные сущности:\n"
        "- employee_name: имя сотрудника\n"
        "- department: отдел\n"
        "- project: проект\n"
        "- date: дата (только в формате дд.мм.гггг)\n"
        "- event_type: тип события\n"
        "- task_keyword: ключ задачи\n"
        "- location: место\n\n"
        'Пример запроса: "Кто из разработки работает 20.05.2025?"\n'
        "Ожидаемый ответ:\n\n"
        '{\n'
        '  "intent": "availability",\n'
        '  "entities": {\n'
        '    "department": "разработка",\n'
        '    "date": "20.05.2025"\n'
        "  }\n"
        "}"
    )

    response = await process_user_query(user_query, system_prompt)
    if response:
        print("Ответ ИИ:")
        print(response)
    else:
        print("Произошла ошибка при обработке запроса пользователя.")


if __name__ == "__main__":
    asyncio.run(main())