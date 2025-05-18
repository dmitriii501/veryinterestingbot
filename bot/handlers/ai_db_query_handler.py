from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import json
from datetime import datetime, timedelta
import dashscope
from bot.config import app_settings

router = Router(name="ai_db_query")


async def get_table_schema():
    return """
    Table: employees
    Columns: id, full_name, department, position, email, birthday, projects, skills, telegram_id
    
    Table: events
    Columns: id, title, description, date, time, location, organizer_id, participants, type
    
    Table: tasks
    Columns: id, title, description, assignee_id, due_date, status, priority, project
    """


async def generate_sql_query(user_query: str, schema: str) -> str:
    if not app_settings.DASHSCOPE_API_KEY:
        return None

    prompt = f"""
    Given the following database schema:
    {schema}
    
    Generate a SQL query to answer this question: "{user_query}"
    Return ONLY the SQL query, nothing else.
    """

    try:
        response = dashscope.Generation.call(
            model='qwen-max',
            prompt=prompt,
            api_key=app_settings.DASHSCOPE_API_KEY,
            result_format='message',
            max_tokens=500,
            temperature=0.1
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content.strip()
        return None
    except Exception as e:
        print(f"Error generating SQL query: {e}")
        return None


@router.message(Command("query"))
async def handle_query_command(message: Message):
    await message.answer(
        "🤖 Отправьте мне вопрос о сотрудниках, мероприятиях или задачах, "
        "и я попробую найти ответ в базе данных.\n\n"
        "Например:\n"
        "- Сколько сотрудников в отделе разработки?\n"
        "- Какие мероприятия запланированы на этой неделе?\n"
        "- Сколько открытых задач с высоким приоритетом?"
    )


@router.message(F.text)
async def process_query(message: Message):
    query = message.text
    bot = message.bot

    try:
        # Получаем схему базы данных
        schema = await get_table_schema()
        
        # Генерируем SQL запрос с помощью AI
        sql_query = await generate_sql_query(query, schema)
        
        if not sql_query:
            await message.answer("😔 Извините, не удалось сгенерировать запрос к базе данных.")
            return

        # Выполняем запрос через Supabase
        result = await bot.supabase_client.rpc(
            'execute_query',
            {'query': sql_query}
        ).execute()

        if not result.data:
            await message.answer("🤔 По вашему запросу ничего не найдено.")
            return

        # Форматируем результат
        response = ["📊 Результаты поиска:"]
        
        if isinstance(result.data, list):
            for item in result.data[:5]:  # Ограничиваем вывод
                response.append("\n" + json.dumps(item, ensure_ascii=False, indent=2))
        else:
            response.append("\n" + json.dumps(result.data, ensure_ascii=False, indent=2))

        await message.answer("\n".join(response))

    except Exception as e:
        await message.answer("😔 Произошла ошибка при выполнении запроса. Попробуйте позже.")
        print(f"Query error: {e}") 