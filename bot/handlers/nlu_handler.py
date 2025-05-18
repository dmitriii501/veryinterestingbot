from aiogram import Router, types
from aiogram.filters import Command
import json
import re

# Предполагается, что process_user_query находится в ai_module/nlu.py
from ai_module.nlu import process_user_query  # Импортируем функцию process_user_query
#from bot.keyboards.inline import *
#from bot.utils.utils import *

router = Router(name="nlu_handler")
#dp = Dispatcher(bot) #Удаляем Bot из инициализации
#Предполагается, что объект bot уже создан и передан в этот модуль.
#Если это не так, вам нужно будет импортировать его и использовать здесь.

def escape_markdown(text: str) -> str:
    """Escape Markdown special characters."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

@router.message(Command("nlu"))
async def nlu_command_handler(message: types.Message):
    """
    Этот обработчик будет вызываться, когда пользователь отправляет команду /nlu.
    Он получает текст сообщения пользователя и отправляет его на обработку в NLU модуль.
    """
    # Extract the actual query (remove the /nlu command)
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(
            "Пожалуйста, укажите текст запроса после команды /nlu\n"
            "Например: /nlu кто из разработки работает сегодня?"
        )
        return

    user_query = command_parts[1]
    
    # Process the query through NLU
    result = await process_user_query(user_query)
    
    if result:
        try:
            # Format the response nicely and escape special characters
            formatted_json = json.dumps(result, ensure_ascii=False, indent=2)
            escaped_response = escape_markdown(formatted_json)
            
            response_text = f"Результат анализа:\n```json\n{escaped_response}\n```"
            await message.answer(response_text, parse_mode="MarkdownV2")
        except Exception as e:
            await message.answer(
                "Произошла ошибка при форматировании ответа. "
                "Попробуйте другой запрос или обратитесь к администратору."
            )
    else:
        await message.answer(
            "Извините, не удалось обработать ваш запрос. "
            "Попробуйте сформулировать его иначе."
        )