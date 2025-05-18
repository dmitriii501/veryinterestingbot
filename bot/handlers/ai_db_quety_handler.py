# bot/handlers/ai_db_query_handler.py
import json
import logging
from typing import Dict, List, Optional, Tuple, Any

from aiogram import Router, types, Bot
from aiogram.filters import Command
from pydantic import ValidationError
from supabase import Client

from bot.utils.database import execute_supabase_query
from bot.utils.db_query_models import DatabaseQuery

router = Router(name="ai_db_query_commands")
logger = logging.getLogger(__name__)


def parse_ai_json_query_with_pydantic(json_string: str) -> Tuple[Optional[DatabaseQuery], Optional[str]]:
    try:
        data = json.loads(json_string)
        query_model = DatabaseQuery.model_validate(data)
        return query_model, None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}")
        return None, f"JSON format error: {e}"
    except ValidationError as e:
        logger.error(f"JSON validation error: {e.errors()}")
        return None, f"Invalid data in JSON: {e.errors()}"


@router.message(Command("db_query"))
async def handle_ai_db_query(message: types.Message, bot: Bot):
    """
    Handle the /db_query command that accepts a JSON payload and queries the database.

    Args:
        message: Message from the user containing the command and JSON query
        bot: Bot instance with supabase_client attribute
    """
    logger.info(f"Received /db_query command from {message.from_user.id}")

    if not hasattr(bot, 'supabase_client') or not bot.supabase_client:
        logger.error("Supabase client not found in bot object.")
        await message.answer("Error: Supabase client is not configured.")
        return

    supabase: Client = bot.supabase_client

    json_payload = message.text.partition(" ")[2].strip()
    if not json_payload:
        await message.answer("Please provide a JSON query after the /db_query command.")
        return

    query_model, error_msg = parse_ai_json_query_with_pydantic(json_payload)
    if error_msg:
        await message.answer(f"Query parsing/validation error: {error_msg}")
        return

    if not query_model:
        await message.answer("Failed to process the query.")
        return

    filters = None
    if query_model.filters:
        filters = [f.model_dump() for f in query_model.filters]

    results, db_error = await execute_supabase_query(
        supabase_client=supabase,
        table_name=query_model.table,
        select_columns=query_model.select_columns,
        filters=filters,
        order_by=query_model.order_by,
        limit=query_model.limit
    )

    if db_error:
        await message.answer(f"Database query execution error: {db_error}")
        return

    if not results:
        await message.answer(f"No results found for your query to table '{query_model.table}'.")
        return

    response_text = f"Results for table '{query_model.table}':\n\n"
    for i, row in enumerate(results):
        row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
        response_text += f"{i + 1}. {row_str}\n"
        if len(response_text) > 3800:
            response_text += "\n... (too much data)"
            break

    await message.answer(response_text)