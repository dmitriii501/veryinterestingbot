# ai_module/nlu.py

import requests
import json
from typing import Optional
from bot.config import settings

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions "

def get_llama3_response(user_message: str) -> Optional[str]:
    """Отправляет запрос к Llama3 через Groq и возвращает ответ"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {Settings.OPENAPI_API_KEY}"
    }

    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "Ты помощник, который отвечает только на русском языке. Не обсуждай политику, религию, споры и провокационные темы. Отвечай кратко, понятно и по сути, без лишних рассуждений."},
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        reply =  response.json()["choices"][0]["message"]["content"]
        await message.answer(reply)

    except Exception as e:
        print(f"Ошибка {e}")
        await message.answer("Попробуйте ещё раз.")

# ✅ Делаем алиас, чтобы можно было импортировать как get_model_response
get_model_response = get_llama3_response  # ✅ Это строка решает проблему


def parse_model_response(text_response: str):
    """Парсим JSON-ответ от модели"""
    if not text_response:
        print("Получен пустой ответ от NLU")
        return None

    try:
        return json.loads(text_response)
    except json.JSONDecodeError as e:
        print(f"[Ошибка парсинга] JSON-ошибка: {str(e)}")
        print(f"Полученный текст: {text_response}")
        return None