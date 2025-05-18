# bot/handlers/ai_intent_handler.py
import json
import logging
from typing import Dict, Callable, Awaitable

from aiogram import Router, types, Bot
from aiogram.filters import Command
from pydantic import ValidationError
from supabase import Client

from bot.utils.database import execute_supabase_query
from bot.utils.ai_request_models import AIRequest, AIRequestEntities

router = Router(name="ai_intent_processing")
logger = logging.getLogger(__name__)


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