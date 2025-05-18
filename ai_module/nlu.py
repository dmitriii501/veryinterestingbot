import requests
import json
import asyncio
from bot.config import app_settings  # Предполагается, что у вас есть этот файл

# Получаем API-ключ из конфигурации
API_KEY = app_settings.AI_API_KEY
MODEL = "google/gemma-3-1b-it:free"  # Или другая модель на ваш выбор


async def chat_with_system_prompt(
    user_message: str, system_prompt: str
) -> str | None:
    """
    Отправляет асинхронный запрос в OpenRouter с системным промптом и возвращает ответ.

    Args:
        user_message: Сообщение пользователя (str).
        system_prompt: Системный промпт для настройки поведения ИИ (str).

    Returns:
        Ответ от OpenRouter (str) в случае успеха, None в случае ошибки.
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    messages = [
        {"role": "system", "content": system_prompt},  # Системный промпт
        {"role": "user", "content": user_message},  # Сообщение пользователя
    ]
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,  # Используем ThreadPoolExecutor по умолчанию для выполнения блокирующего вызова
            lambda: requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            ),
        )
        response.raise_for_status()  # Вызываем исключение для статус-кодов 4xx и 5xx

        response_json = response.json()
        if response_json and response_json["choices"]:
            content = response_json["choices"][0]["message"]["content"]
            return content.replace("<think>", "").replace(
                "</think>", ""
            ).strip()
        else:
            print("Предупреждение: OpenRouter вернул пустой ответ.")
            return None  # Возвращаем None при пустом ответе
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к OpenRouter: {e}")
        return None  # Возвращаем None при ошибке запроса
    except json.JSONDecodeError:
        print("Ошибка при обработке ответа: Некорректный JSON от OpenRouter")
        return None  # Возвращаем None при ошибке JSON
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        return None  # Возвращаем None при любой другой ошибке


async def process_user_query(
    user_query: str, system_prompt: str
) -> str | None:
    """
    Отправляет запрос пользователя в OpenRouter с системным промптом и возвращает ответ.

    Args:
        user_query: Запрос пользователя (str).
        system_prompt: Системный промпт для настройки поведения ИИ (str).

    Returns:
        Ответ от OpenRouter (str) в случае успеха, None в случае ошибки.
    """
    response = await chat_with_system_prompt(user_query, system_prompt)
    return response


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