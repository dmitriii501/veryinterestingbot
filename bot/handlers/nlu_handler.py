from aiogram import Router, Bot, F
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
    """
    if info_type:
        if info_type == "education":
            return f"🎓 Образование сотрудника {employee['name']}:\n{employee.get('education', 'не указано')}"
        elif info_type == "hire_date":
            hire_date = employee.get('hire_date')
            if hire_date:
                date_obj = datetime.strptime(hire_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d.%m.%Y")
                return f"📅 Дата приема на работу {employee['name']}:\n{formatted_date}"
            return f"📅 Дата приема на работу {employee['name']}: не указана"
        elif info_type == "job_title":
            return f"💼 Должность сотрудника {employee['name']}:\n{employee.get('job_title', 'не указана')}"
        elif info_type == "phone_number":
            phone = str(employee.get('phone_number', ''))
            if phone:
                formatted_phone = f"+{phone[:1]} ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:]}"
                return f"📱 Телефон сотрудника {employee['name']}:\n{formatted_phone}"
            return f"📱 Телефон сотрудника {employee['name']}: не указан"
    
    # Если тип информации не указан, возвращаем общую информацию
    info = [f"👤 Информация о сотруднике {employee['name']}:"]
    if employee.get('job_title'):
        info.append(f"💼 Должность: {employee['job_title']}")
    if employee.get('department'):
        info.append(f"🏢 Отдел: {employee['department']}")
    if employee.get('hire_date'):
        date_obj = datetime.strptime(employee['hire_date'], "%Y-%m-%d")
        info.append(f"📅 Дата приема: {date_obj.strftime('%d.%m.%Y')}")
    if employee.get('education'):
        info.append(f"🎓 Образование: {employee['education']}")
    if employee.get('phone_number'):
        phone = str(employee['phone_number'])
        formatted_phone = f"+{phone[:1]} ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:]}"
        info.append(f"📱 Телефон: {formatted_phone}")
    
    return "\n".join(info)

async def find_employees(bot: Bot, query: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Ищет сотрудников в базе данных по различным критериям.
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
    Обработчик команды /nlu для поиска информации о сотрудниках.
    """
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(
            "ℹ️ Пожалуйста, укажите ваш запрос после команды /nlu\n\n"
            "Примеры запросов:\n"
            "🎓 /nlu какое образование у Виктора Ивановича\n"
            "💼 /nlu кто работает юристом\n"
            "📅 /nlu когда приняли на работу Анну\n"
            "ℹ️ /nlu дай информацию о Петре Васильевиче"
        )
        return

    user_query = command_parts[1]
    result = await process_user_query(user_query)
    
    if result:
        try:
            employees = await find_employees(message.bot, result)
            
            if not employees:
                await message.answer("❌ Извините, не удалось найти сотрудников по вашему запросу.")
                return
                
            if result['intent'] in ['find_employee', 'find_by_position', 'find_by_department']:
                info_type = result.get('entities', {}).get('info_type')
                
                if len(employees) == 1:
                    # Один сотрудник - показываем подробную информацию
                    response = format_employee_info(employees[0], info_type)
                    await message.answer(response)
                else:
                    # Несколько сотрудников - показываем список
                    if result.get('intent') == 'find_by_position':
                        position = result.get('entities', {}).get('position', 'указанной должности')
                        response = [f"👥 Сотрудники на должности {position}:"]
                    elif result.get('intent') == 'find_by_department':
                        department = result.get('entities', {}).get('department', 'указанном отделе')
                        response = [f"👥 Сотрудники в отделе {department}:"]
                    else:
                        response = ["👥 Найденные сотрудники:"]
                    
                    for emp in employees:
                        emp_info = f"• {emp['name']}"
                        if emp.get('job_title'):
                            emp_info += f" 💼 {emp['job_title']}"
                        if emp.get('department'):
                            emp_info += f" 🏢 {emp['department']}"
                        response.append(emp_info)
                    
                    await message.answer("\n".join(response))
                else:
                    await message.answer("❌ Извините, я не смог правильно определить тип запроса.")
                
        except Exception as e:
            logging.error(f"Error processing response: {e}")
            await message.answer(
                "❌ Произошла ошибка при обработке запроса. "
                "Попробуйте сформулировать его иначе или обратитесь к администратору."
            )
    else:
        await message.answer(
            "❌ Извините, не удалось обработать ваш запрос. "
            "Попробуйте сформулировать его иначе."
        )