from aiogram import Router, Bot
from aiogram import types
from aiogram.filters import Command
import json
import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

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

def format_employee_info(employee: Dict[str, Any], info_type: Optional[str] = None) -> str:
    """
    Форматирует информацию о сотруднике в зависимости от запрошенного типа информации.
    
    Args:
        employee: Словарь с данными сотрудника
        info_type: Тип запрашиваемой информации (education, hire_date, phone_number, job_title)
        
    Returns:
        Отформатированная строка с информацией
    """
    if info_type:
        if info_type == "education":
            return f"Образование сотрудника {employee['name']}: {employee.get('education', 'не указано')}"
        elif info_type == "hire_date":
            hire_date = employee.get('hire_date')
            if hire_date:
                date_obj = datetime.strptime(hire_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d.%m.%Y")
                return f"Дата приема на работу {employee['name']}: {formatted_date}"
            return f"Дата приема на работу {employee['name']}: не указана"
        elif info_type == "job_title":
            return f"Должность сотрудника {employee['name']}: {employee.get('job_title', 'не указана')}"
        elif info_type == "phone_number":
            phone = str(employee.get('phone_number', ''))
            if phone:
                return f"Телефон сотрудника {employee['name']}: +{phone[:1]} ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:]}"
            return f"Телефон сотрудника {employee['name']}: не указан"
    
    # Если тип информации не указан, возвращаем общую информацию
    info = [f"Информация о сотруднике {employee['name']}:"]
    if employee.get('job_title'):
        info.append(f"Должность: {employee['job_title']}")
    if employee.get('department'):
        info.append(f"Отдел: {employee['department']}")
    if employee.get('hire_date'):
        date_obj = datetime.strptime(employee['hire_date'], "%Y-%m-%d")
        info.append(f"Дата приема: {date_obj.strftime('%d.%m.%Y')}")
    if employee.get('education'):
        info.append(f"Образование: {employee['education']}")
    if employee.get('phone_number'):
        phone = str(employee['phone_number'])
        info.append(f"Телефон: +{phone[:1]} ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:]}")
    
    return "\n".join(info)

async def find_employees(bot: Bot, query: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Ищет сотрудников в базе данных по различным критериям.
    
    Args:
        bot: Экземпляр бота с подключением к Supabase
        query: Словарь с параметрами поиска
        
    Returns:
        Список найденных сотрудников
    """
    try:
        if not bot.supabase_client:
            logging.error("Supabase client not configured")
            return []
            
        supabase_query = bot.supabase_client.table('employees').select('*')
        
        # Поиск по имени
        if query.get('entities', {}).get('employee_name'):
            supabase_query = supabase_query.ilike('name', f"%{query['entities']['employee_name']}%")
            
        # Поиск по должности
        if query.get('entities', {}).get('position'):
            supabase_query = supabase_query.ilike('job_title', f"%{query['entities']['position']}%")
            
        # Поиск по отделу
        if query.get('entities', {}).get('department'):
            supabase_query = supabase_query.ilike('department', f"%{query['entities']['department']}%")
            
        response = supabase_query.execute()
        return response.data if response.data else []
        
    except Exception as e:
        logging.error(f"Error querying Supabase for employees: {e}")
        return []

@router.message(Command("nlu"))
async def nlu_command_handler(message: types.Message):
    """
    Этот обработчик будет вызываться, когда пользователь отправляет команду /nlu.
    Он получает текст сообщения пользователя и отправляет его на обработку в NLU модуль.
    """
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(
            "Пожалуйста, укажите текст запроса после команды /nlu\n"
            "Например:\n"
            "- /nlu какое образование у Виктора Ивановича\n"
            "- /nlu кто работает юристом\n"
            "- /nlu когда приняли на работу Анну\n"
            "- /nlu дай информацию о Петре Васильевиче"
        )
        return

    user_query = command_parts[1]
    result = await process_user_query(user_query)
    
    if result:
        try:
            # Поиск сотрудников в зависимости от интента
            employees = await find_employees(message.bot, result)
            
            if not employees:
                await message.answer("Извините, не удалось найти сотрудников по вашему запросу.")
                return
                
            # Формируем ответ в зависимости от интента и найденных сотрудников
            if result['intent'] in ['find_employee', 'find_by_position', 'find_by_department']:
                info_type = result.get('entities', {}).get('info_type')
                
                if len(employees) == 1:
                    # Если найден один сотрудник, показываем подробную информацию
                    response = format_employee_info(employees[0], info_type)
                    await message.answer(response)
                else:
                    # Если найдено несколько сотрудников, показываем список
                    response = "Найденные сотрудники:\n\n"
                    for emp in employees:
                        response += f"• {emp['name']}"
                        if emp.get('job_title'):
                            response += f" - {emp['job_title']}"
                        response += "\n"
                    await message.answer(response.strip())
            
                
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