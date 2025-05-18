import requests
import json
import os
from bot.config import app_settings

# Получаем API-ключ из конфигурации
API_KEY = app_settings.AI_API_KEY
MODEL = "google/gemma-3-1b-it:free"  # Можно заменить на нужную модель OpenRouter

print("[DEBUG] AI_API_KEY из .env:", os.getenv("AI_API_KEY"))
print("[DEBUG] API_KEY из app_settings:", API_KEY)
print(repr(os.getenv("AI_API_KEY")))


def log_openrouter_response(response):
    print("[DEBUG] OpenRouter response object:", response)
    print("[DEBUG] status_code:", response.status_code)
    try:
        print("[DEBUG] response.json():", response.json())
    except Exception as e:
        print("[DEBUG] Ошибка при выводе response.json():", e)


async def process_user_query(user_query: str, system_prompt: str) -> str | None:
    """
    Отправляет запрос пользователя в OpenRouter и возвращает ответ.
    """
    if not API_KEY:
        print("ОШИБКА: API ключ OpenRouter не настроен")
        return None

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }

    print("[DEBUG] Отправляемый messages:", messages)
    print("[DEBUG] Используемый API_KEY:", API_KEY)

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        log_openrouter_response(response)
        response.raise_for_status()
        response_json = response.json()
        if response_json and response_json.get("choices"):
            content = response_json["choices"][0]["message"]["content"]
            return content.strip()
        else:
            print("[DEBUG] OpenRouter вернул пустой ответ.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к OpenRouter: {e}")
        return None
    except json.JSONDecodeError:
        print("Ошибка при обработке ответа: Некорректный JSON от OpenRouter")
        return None
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
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