import requests
import json
import asyncio
from bot.config import app_settings  # Предполагается, что у вас есть этот файл

# Получаем API-ключ из конфигурации
API_KEY = app_settings.AI_API_KEY
MODEL = "deepseek/deepseek-r1"  # Или другая модель на ваш выбор


async def chat_with_system_prompt(user_message: str, system_prompt: str) -> str | None:
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
            return content.replace("<think>", "").replace("</think>", "").strip()
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

async def process_user_query(user_query: str, system_prompt: str) -> str | None:
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
    user_query = "Привет, OpenRouter! Как дела?"
    system_prompt = "Отвечай как дружелюбный ассистент."

    response = await process_user_query(user_query, system_prompt)
    if response:
        print("Ответ ИИ:")
        print(response)
    else:
        print("Произошла ошибка при обработке запроса пользователя.")



if __name__ == "__main__":
    asyncio.run(main())
