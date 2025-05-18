from aiogram import Router, types
from aiogram.filters import Command
import json
import re
import logging

# Предполагается, что process_user_query находится в ai_module/nlu.py
from ai_module.nlu import process_user_query  # Импортируем функцию process_user_query
#from bot.keyboards.inline import *
#from bot.utils.utils import *

router = Router(name="nlu_handler")
#dp = Dispatcher(bot) #Удаляем Bot из инициализации
#Предполагается, что объект bot уже создан и передан в этот модуль.
#Если это не так, вам нужно будет импортировать его и использовать здесь.

def escape_markdown_v2(text: str) -> str:
    """Escape MarkdownV2 special characters."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in escape_chars else c for c in text)

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
            # Format the response nicely
            formatted_json = json.dumps(result, ensure_ascii=False, indent=2)
            
            # Split the JSON into lines and escape each line separately
            escaped_lines = [escape_markdown_v2(line) for line in formatted_json.split('\n')]
            escaped_response = '\n'.join(escaped_lines)
            
            # Construct the final message with code block
            response_text = f"Результат анализа:\n```json\n{escaped_response}\n```"
            
            try:
                await message.answer(response_text, parse_mode="MarkdownV2")
            except Exception as e:
                # If MarkdownV2 formatting fails, try sending without formatting
                logging.error(f"Failed to send formatted message: {e}")
                await message.answer(
                    f"Результат анализа:\n{formatted_json}",
                    parse_mode=None
                )
        except Exception as e:
            logging.error(f"Error formatting NLU response: {e}")
            await message.answer(
                "Произошла ошибка при форматировании ответа. "
                "Попробуйте другой запрос или обратитесь к администратору."
            )
    else:
        await message.answer(
            "Извините, не удалось обработать ваш запрос. "
            "Попробуйте сформулировать его иначе."
        )