# bot/handlers/ai_intent_handler.py
import json
import logging
from typing import Dict, Callable, Awaitable, Optional

from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from pydantic import ValidationError
from supabase import Client
import dashscope
from bot.config import app_settings

from bot.utils.database import execute_supabase_query
from bot.utils.ai_request_models import AIRequest, AIRequestEntities

from ai_module.nlu import NLUProcessor, process_user_query
from ai_module.response_generator import ResponseGenerator

router = Router(name="ai_intent_handler")
logger = logging.getLogger(__name__)

# Initialize processors
nlu_processor = NLUProcessor()


async def handle_find_employee(entities: AIRequestEntities, supabase: Client) -> str:
    logger.info(f"Processing intent: find_employee, Entities: {entities}")
    filters = []

    if entities.employee_name:
        filters.append({'column': 'name', 'operator': 'ilike', 'value': f"%{entities.employee_name}%"})

    if entities.department:
        filters.append({'column': 'department_name', 'operator': 'ilike', 'value': f"%{entities.department}%"})

    if not filters:
        return "Please specify an employee name or department for search."

    data, error = await execute_supabase_query(
        supabase_client=supabase,
        table_name="employees",
        select_columns="name, job_title, phone_number, department_name",
        filters=filters,
        limit=5
    )

    if error:
        return f"Error searching for employee: {error}"

    if not data:
        return "No employees found matching your request."

    response = "Found employees:\n"
    for emp in data:
        response += f"- {emp.get('name', 'N/A')} ({emp.get('job_title', 'N/A')}), Dept: {emp.get('department_name', 'N/A')}, Tel: {emp.get('phone_number', 'N/A')}\n"

    return response


async def handle_availability(entities: AIRequestEntities, supabase: Client) -> str:
    logger.info(f"Processing intent: availability, Entities: {entities}")
    filters = []
    response_intro = "Checking availability"

    if entities.employee_name:
        filters.append({'column': 'name', 'operator': 'ilike', 'value': f"%{entities.employee_name}%"})
        response_intro += f" for {entities.employee_name}"

    if entities.department:
        filters.append({'column': 'department_name', 'operator': 'ilike', 'value': f"%{entities.department}%"})
        if not entities.employee_name:  # If name not specified, search by department
            response_intro += f" in department {entities.department}"

    if entities.date:
        response_intro += f" on {entities.date}"

    if not filters:
        return "To check availability, please specify an employee or department."

    data, error = await execute_supabase_query(
        supabase_client=supabase,
        table_name="employees",
        select_columns="name, job_title",
        filters=filters,
        limit=5
    )

    if error:
        return f"Error: {error}"

    if not data:
        return f"{response_intro}: No employees found."

    response = f"{response_intro}:\n"
    for emp in data:
        availability_status = "presumably available (actual verification needed)"
        response += f"- {emp.get('name', 'N/A')}: {availability_status}\n"

    if not entities.date:
        response += "\n(Date not specified, cannot check availability for a specific day)"

    return response


async def handle_unknown_intent(entities: AIRequestEntities, supabase: Client) -> str:
    logger.info(f"Processing unknown intent or general question. Entities: {entities}")
    return "Sorry, I don't quite understand your request or this is a general question. Please try rephrasing."


# Map of intent types to their handler functions
INTENT_HANDLERS: Dict[str, Callable[[AIRequestEntities, Client], Awaitable[str]]] = {
    "find_employee": handle_find_employee,
    "availability": handle_availability,
    "unknown": handle_unknown_intent,
    "general_question": handle_unknown_intent,
}


@router.message(Command("ask_ai"))
async def process_ai_request(message: types.Message, bot: Bot):
    logger.debug(f"Received message for AI processing: {message.text}")

    if not hasattr(bot, 'supabase_client') or not bot.supabase_client:
        logger.error("Supabase client not found in bot object.")
        await message.answer("Error: Supabase client is not configured.")
        return

    supabase: Client = bot.supabase_client

    json_payload = message.text.partition(" ")[2].strip()
    if not json_payload:
        await message.answer("Please provide a JSON request from AI after the command.")
        return

    try:
        ai_data = json.loads(json_payload)
        ai_request = AIRequest.model_validate(ai_data)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from AI: {e}")
        await message.answer(f"Invalid JSON from AI: {e}")
        return
    except ValidationError as e:
        logger.error(f"Error validating data from AI: {e.errors()}")
        await message.answer(f"Invalid data in JSON from AI: {e.errors()}")
        return

    handler_function = INTENT_HANDLERS.get(ai_request.intent, handle_unknown_intent)

    entities_to_pass = ai_request.entities if ai_request.entities else AIRequestEntities()

    response_text = await handler_function(entities_to_pass, supabase)

    await message.answer(response_text)


async def classify_intent(text: str) -> dict:
    """
    Классифицирует намерение пользователя с помощью AI.
    """
    if not app_settings.DASHSCOPE_API_KEY:
        return {"intent": "unknown", "confidence": 0}

    prompt = f"""
    Classify the following user message into one of these intents:
    - search_employee (поиск сотрудника)
    - search_event (поиск мероприятия)
    - search_task (поиск задачи)
    - create_event (создание мероприятия)
    - create_task (создание задачи)
    - update_status (обновление статуса)
    - unknown (неизвестное намерение)

    Message: "{text}"

    Return ONLY a JSON object with 'intent' and 'confidence' fields.
    Example: {{"intent": "search_employee", "confidence": 0.95}}
    """

    try:
        response = dashscope.Generation.call(
            model='qwen-max',
            prompt=prompt,
            api_key=app_settings.DASHSCOPE_API_KEY,
            result_format='message',
            max_tokens=100,
            temperature=0.1
        )
        
        if response.status_code == 200:
            return eval(response.output.choices[0].message.content.strip())
        return {"intent": "unknown", "confidence": 0}
    except Exception as e:
        print(f"Error classifying intent: {e}")
        return {"intent": "unknown", "confidence": 0}


async def extract_entities(text: str, intent: str) -> dict:
    """
    Извлекает сущности из текста пользователя в зависимости от намерения.
    """
    if not app_settings.DASHSCOPE_API_KEY:
        return {}

    entity_types = {
        "search_employee": ["name", "department", "position", "skills"],
        "search_event": ["title", "date", "type"],
        "search_task": ["title", "status", "priority", "project"],
        "create_event": ["title", "description", "date", "time", "location", "type"],
        "create_task": ["title", "description", "assignee", "due_date", "priority", "project"],
        "update_status": ["entity_type", "entity_id", "new_status"]
    }

    if intent not in entity_types:
        return {}

    prompt = f"""
    Extract the following entities from the text: {entity_types[intent]}
    
    Text: "{text}"
    
    Return ONLY a JSON object where keys are entity names and values are extracted values.
    If an entity is not found, don't include it in the response.
    Example: {{"name": "John", "department": "IT"}}
    """

    try:
        response = dashscope.Generation.call(
            model='qwen-max',
            prompt=prompt,
            api_key=app_settings.DASHSCOPE_API_KEY,
            result_format='message',
            max_tokens=200,
            temperature=0.1
        )
        
        if response.status_code == 200:
            return eval(response.output.choices[0].message.content.strip())
        return {}
    except Exception as e:
        print(f"Error extracting entities: {e}")
        return {}


@router.message(F.text & ~Command(commands=["start", "help", "nlu"]))
async def handle_user_message(message: types.Message, bot: Bot):
    """
    Process user messages through the two-stage AI pipeline:
    1. NLU processing to extract intent and entities
    2. Response generation based on the extracted information and database data
    """
    if not hasattr(bot, 'supabase_client') or not bot.supabase_client:
        logger.error("Supabase client not configured")
        await message.answer("Извините, возникла ошибка конфигурации. Обратитесь к администратору.")
        return

    # Stage 1: NLU Processing
    logger.info(f"Processing message: {message.text}")
    nlu_result = await process_user_query(message.text)
    
    if not nlu_result:
        await message.answer(
            "Извините, я не смог правильно понять ваш запрос. "
            "Попробуйте сформулировать его иначе."
        )
        return

    # Log NLU result
    logger.info(f"NLU Result: {json.dumps(nlu_result, ensure_ascii=False)}")

    # Stage 2: Response Generation
    try:
        response_generator = ResponseGenerator(bot.supabase_client)
        response = await response_generator.generate_response(nlu_result)
        
        if response:
            await message.answer(response)
        else:
            await message.answer(
                "Извините, произошла ошибка при обработке вашего запроса. "
                "Попробуйте позже или обратитесь к администратору."
            )
    except Exception as e:
        logger.error(f"Error in response generation: {e}")
        await message.answer(
            "Извините, произошла ошибка при формировании ответа. "
            "Попробуйте позже или обратитесь к администратору."
        )


async def create_event(message: types.Message, entities: dict):
    try:
        result = await message.bot.supabase_client.table("events").insert({
            "title": entities["title"],
            "description": entities.get("description", ""),
            "date": entities["date"],
            "time": entities.get("time"),
            "location": entities.get("location"),
            "organizer_id": message.from_user.id,
            "type": entities.get("type", "other")
        }).execute()
        
        await message.answer("✅ Мероприятие успешно создано!")
    except Exception as e:
        await message.answer("❌ Не удалось создать мероприятие. Попробуйте позже.")
        print(f"Error creating event: {e}")


async def create_task(message: types.Message, entities: dict):
    try:
        result = await message.bot.supabase_client.table("tasks").insert({
            "title": entities["title"],
            "description": entities.get("description", ""),
            "assignee_id": message.from_user.id,  # По умолчанию назначаем на создателя
            "due_date": entities["due_date"],
            "status": "pending",
            "priority": entities.get("priority", "medium"),
            "project": entities.get("project")
        }).execute()
        
        await message.answer("✅ Задача успешно создана!")
    except Exception as e:
        await message.answer("❌ Не удалось создать задачу. Попробуйте позже.")
        print(f"Error creating task: {e}")


async def update_status(message: types.Message, entities: dict):
    try:
        table = entities["entity_type"] + "s"  # events или tasks
        result = await message.bot.supabase_client.table(table).update({
            "status": entities["new_status"]
        }).eq("id", entities["entity_id"]).execute()
        
        await message.answer("✅ Статус успешно обновлен!")
    except Exception as e:
        await message.answer("❌ Не удалось обновить статус. Попробуйте позже.")
        print(f"Error updating status: {e}")