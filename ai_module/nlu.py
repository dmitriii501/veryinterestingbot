import json
import dashscope
import os
from bot.config import app_settings

# Получаем API-ключ из конфигурации
API_KEY = app_settings.DASHSCOPE_API_KEY

print("[DEBUG] DASHSCOPE_API_KEY из .env:", os.getenv("DASHSCOPE_API_KEY"))
print("[DEBUG] API_KEY из app_settings:", API_KEY)


def log_dashscope_response(response):
    print("[DEBUG] DashScope response object:", response)
    if hasattr(response, 'status_code'):
        print("[DEBUG] status_code:", response.status_code)
    if hasattr(response, 'output'):
        print("[DEBUG] output:", response.output)
    if hasattr(response, 'code'):
        print("[DEBUG] code:", getattr(response, 'code', None))
    if hasattr(response, 'message'):
        print("[DEBUG] message:", getattr(response, 'message', None))


async def process_user_query(user_query: str, system_prompt: str) -> str | None:
    """
    Отправляет запрос пользователя в DashScope и возвращает ответ.

    Args:
        user_query: Запрос пользователя (str).
        system_prompt: Системный промпт для настройки поведения ИИ (str).

    Returns:
        Ответ от DashScope (str) в случае успеха, None в случае ошибки.
    """
    if not API_KEY:
        print("ОШИБКА: API ключ DashScope не настроен")
        return None

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]

        print("[DEBUG] Отправляемый messages:", messages)
        print("[DEBUG] Используемый API_KEY:", API_KEY)

        response = dashscope.Generation.call(
            model='qwen-max',
            messages=messages,
            api_key=API_KEY,
            result_format='message',
            max_tokens=1000,
            temperature=0.1
        )

        log_dashscope_response(response)
        
        if response.status_code == 200:
            print("[DEBUG] Успешный ответ DashScope")
            return response.output.choices[0].message.content.strip()
        else:
            print(f"Ошибка DashScope API: {getattr(response, 'code', None)} - {getattr(response, 'message', None)}")
            return None

    except Exception as e:
        print(f"Ошибка при обработке запроса: {e}")
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