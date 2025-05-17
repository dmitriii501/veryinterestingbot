from aiogram import Router, types, F
from aiogram.filters import Command
import requests
from config.settings import Settings

router = Router()


@router.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer_photo(photo='https://upload.wikimedia.org/wikipedia/commons/1/12/%D0%A3%D1%80%D0%90%D0%93%D0%A1.jpg', caption="Привет! Я твой ассистент по расписанию!")

@router.message(Command("help"))
async def start_handler(message: types.message):
    await message.answer("Появится в будущем...")

@router.message()
async def llama3_handler(message: types.Message):
    user_input = message.text

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
