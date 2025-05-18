from aiogram import Router, Bot
from aiogram import types
from aiogram.filters import Command
import json
import re
import logging
from typing import Optional

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

async def find_employee_phone(bot: Bot, employee_name: str) -> Optional[str]:
    """
    Ищет номер телефона сотрудника в базе данных Supabase.
    
    Args:
        bot: Экземпляр бота с подключением к Supabase
        employee_name: Имя сотрудника для поиска
        
    Returns:
        Строка с отформатированным номером телефона или None, если не найден
    """
    try:
        if not bot.supabase_client:
            logging.error("Supabase client not configured")
            return None
            
        # Выполняем поиск по имени (используем ILIKE для регистронезависимого поиска)
        response = bot.supabase_client.table('employees').select('name, phone_number').ilike('name', f'%{employee_name}%').execute()
        
        if not response.data:
            return None
            
        # Если найдено несколько сотрудников, берем первого
        employee = response.data[0]
        if employee.get('phone_number'):
            # Форматируем номер телефона для вывода
            phone = str(employee['phone_number'])
            return f"+{phone[:1]} ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:]}"
        return None
        
    except Exception as e:
        logging.error(f"Error querying Supabase for employee phone: {e}")
        return None

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
            # Format the response nicely for debug output
            formatted_json = json.dumps(result, ensure_ascii=False, indent=2)
            
            # If intent is find_employee and we have an employee name, try to find their phone
            if result.get('intent') == 'find_employee' and result.get('entities', {}).get('employee_name'):
                employee_name = result['entities']['employee_name']
                phone_number = await find_employee_phone(message.bot, employee_name)
                
                if phone_number:
                    await message.answer(
                        f"Телефон сотрудника {employee_name}:\n{phone_number}"
                    )
                else:
                    await message.answer(
                        f"Извините, не удалось найти номер телефона для сотрудника {employee_name}"
                    )
                    
                # Also show the NLU debug info
                escaped_lines = [escape_markdown_v2(line) for line in formatted_json.split('\n')]
                escaped_response = '\n'.join(escaped_lines)
                debug_text = f"Детали анализа запроса:\n```json\n{escaped_response}\n```"
                
                try:
                    await message.answer(debug_text, parse_mode="MarkdownV2")
                except Exception as e:
                    logging.error(f"Failed to send debug info: {e}")
            else:
                # For other intents, just show the NLU analysis
                escaped_lines = [escape_markdown_v2(line) for line in formatted_json.split('\n')]
                escaped_response = '\n'.join(escaped_lines)
                response_text = f"Результат анализа:\n```json\n{escaped_response}\n```"
                
                try:
                    await message.answer(response_text, parse_mode="MarkdownV2")
                except Exception as e:
                    logging.error(f"Failed to send formatted message: {e}")
                    await message.answer(
                        f"Результат анализа:\n{formatted_json}",
                        parse_mode=None
                    )
        except Exception as e:
            logging.error(f"Error processing response: {e}")
            await message.answer(
                "Произошла ошибка при обработке ответа. "
                "Попробуйте другой запрос или обратитесь к администратору."
            )
    else:
        await message.answer(
            "Извините, не удалось обработать ваш запрос. "
            "Попробуйте сформулировать его иначе."
        )