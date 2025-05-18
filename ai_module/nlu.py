import os
from bot.config import app_settings
from openai import OpenAI

# Получаем API-ключ из конфигурации
API_KEY = app_settings.AI_API_KEY
NSCALE_BASE_URL = "https://inference.api.nscale.com/v1"
MODEL = "Qwen/Qwen3-235B-A22B"

print("[DEBUG] AI_API_KEY из .env:", os.getenv("AI_API_KEY"))
print("[DEBUG] API_KEY из app_settings:", API_KEY)

client = OpenAI(
    api_key=API_KEY,
    base_url=NSCALE_BASE_URL
)

def log_nscale_response(response):
    print("[DEBUG] Nscale response object:", response)
    if hasattr(response, 'choices'):
        print("[DEBUG] choices:", response.choices)
    if hasattr(response, 'usage'):
        print("[DEBUG] usage:", response.usage)


async def process_user_query(user_query: str, system_prompt: str) -> str | None:
    """
    Отправляет запрос пользователя в Nscale (через OpenAI совместимый API) и возвращает ответ.
    """
    if not API_KEY:
        print("ОШИБКА: API ключ Nscale не настроен")
        return None

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]

    print("[DEBUG] Отправляемый messages:", messages)
    print("[DEBUG] Используемый API_KEY:", API_KEY)
    print("[DEBUG] Используемый base_url:", NSCALE_BASE_URL)
    print("[DEBUG] Используемая модель:", MODEL)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        log_nscale_response(response)
        if response.choices and response.choices[0].message:
            return response.choices[0].message.content.strip()
        else:
            print("[DEBUG] Nscale вернул пустой ответ.")
            return None
    except Exception as e:
        print(f"Ошибка при запросе к Nscale: {e}")
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