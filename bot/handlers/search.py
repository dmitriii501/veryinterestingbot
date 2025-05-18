from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from bot.models import Employee, Event, Task
from datetime import datetime

router = Router(name="search")


@router.message(Command("search"))
async def search_command(message: Message):
    await message.answer(
        "🔍 Отправьте мне поисковый запрос в свободной форме.\n"
        "Например:\n"
        "- Кто работает в отделе разработки?\n"
        "- Какие мероприятия запланированы на следующей неделе?\n"
        "- Найти задачи с высоким приоритетом"
    )


@router.message(F.text)
async def process_search_query(message: Message):
    query = message.text.lower()
    bot = message.bot
    
    try:
        # Поиск сотрудников
        employees = await bot.supabase_client.table("employees").select("*").execute()
        
        # Поиск мероприятий
        events = await bot.supabase_client.table("events").select("*").execute()
        
        # Поиск задач
        tasks = await bot.supabase_client.table("tasks").select("*").execute()

        # Преобразование результатов в модели
        employees_data = [Employee(**emp) for emp in employees.data]
        events_data = [Event(**event) for event in events.data]
        tasks_data = [Task(**task) for task in tasks.data]

        # Фильтрация результатов на основе запроса
        found_employees = [
            emp for emp in employees_data
            if query in emp.full_name.lower() or
            query in emp.department.lower() or
            any(query in proj.lower() for proj in emp.projects)
        ]

        found_events = [
            event for event in events_data
            if query in event.title.lower() or
            query in event.description.lower()
        ]

        found_tasks = [
            task for task in tasks_data
            if query in task.title.lower() or
            query in task.description.lower()
        ]

        # Формирование ответа
        response = []
        
        if found_employees:
            response.append("👥 Найденные сотрудники:")
            for emp in found_employees[:5]:  # Ограничиваем вывод
                response.append(f"- {emp.full_name} ({emp.department})")
        
        if found_events:
            response.append("\n📅 Найденные мероприятия:")
            for event in found_events[:5]:
                response.append(f"- {event.title} ({event.date})")
        
        if found_tasks:
            response.append("\n📋 Найденные задачи:")
            for task in found_tasks[:5]:
                response.append(f"- {task.title} ({task.status})")

        if not response:
            await message.answer("🤔 По вашему запросу ничего не найдено.")
            return

        await message.answer("\n".join(response))

    except Exception as e:
        await message.answer("😔 Произошла ошибка при поиске. Попробуйте позже.")
        print(f"Search error: {e}")
