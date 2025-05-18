# bot/handlers/employees_handler.py
import logging
from aiogram import Router, types, Bot
from aiogram.types import Message
from aiogram.filters import Command
from supabase import Client

from  bot.utils.database import fetch_data_from_table

router = Router(name="employees_commands")
logger = logging.getLogger(__name__)

@router.message(Command("get_employees"))
async def get_employees_command(message: Message, bot: Bot):
    logger.info(f"Получена команда /get_employees от пользователя {message.from_user.id}")

    if not hasattr(bot, 'supabase_client') or not bot.supabase_client:
        logger.error("Клиент Supabase не найден в объекте бота.")
        await message.answer("Извините, произошла ошибка на сервере. Не удалось подключиться к базе данных.")
        return

    supabase: Client = bot.supabase_client

    table_name = 'employees'

    columns_to_select = "name, hire_date, department, phone_number, job_title"

    logger.debug(f"Запрос данных из таблицы '{table_name}', колонки: '{columns_to_select}'")
    employees_list, error = await fetch_data_from_table(supabase, table_name, columns=columns_to_select)

    if error:
        logger.error(f"Ошибка при получении данных из Supabase: {error}")
        await message.answer(f"Не удалось получить список сотрудников: {error}")
        return

    if not employees_list:
        logger.info(f"Данные в таблице '{table_name}' не найдены.")
        await message.answer(f"В таблице '{table_name}' нет данных или они не были загружены.")
        return

    logger.info(f"Получено {len(employees_list)} записей из таблицы '{table_name}'.")

    response_text = f"👥 Список сотрудников (из таблицы '{table_name}'):\n\n"
    for i, employee in enumerate(employees_list):
        name = employee.get('name', 'N/A')
        hire_date = employee.get('hire_date', 'N/A')
        department = employee.get('department', 'N/A')
        phone = employee.get('phone_number', 'N/A')
        job_title = employee.get('job_title', 'N/A')

        entry = f"{i + 1}. 🧑‍💼 ФИО: {name}\n" \
                f"   Отдел: {department}\n" \
                f"   📞 Телефон: {phone}\n" \
                f"   📅 Дата приема: {hire_date}\n" \
                f"    Должность: {job_title}\n"
        response_text += entry + "\n"

        if len(response_text) > 3800:  # Оставляем запас
            response_text += "... (данных слишком много, показана часть)"
            logger.warning("Ответ слишком длинный, обрезаем.")
            break

    await  message.answer(response_text)