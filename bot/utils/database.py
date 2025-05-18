import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from supabase import Client, create_client

logger = logging.getLogger(__name__)

async def fetch_data_from_table(
        supabase_client: Client,
        table_name: str,
        columns: str = '*'
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    if not supabase_client:
        logger.error("Клиент Supabase не был предоставлен функции fetch_data_from_table.")
        return None, "Клиент Supabase не инициализирован."
    try:
        logger.debug(f"Выполнение запроса к Supabase: таблица='{table_name}', колонки='{columns}'")
        response = await asyncio.to_thread(
            supabase_client.table(table_name).select(columns).execute
        )
        if hasattr(response,'data'):
            logger.debug(f"Получен ответ от Supabase, количество записей: {len(response.data)}")
            return response.data, None
        else:
            logger.warning(f"Неожиданный формат ответа от Supabase для таблицы {table_name}: {response}")
            return None, f"Неожиданный формат ответа от Supabase для таблицы {table_name}."
    except Exception as e:
        logger.error(f"Ошибка при запросе к Supabase (таблица {table_name}): {e}", exc_info=True)
        return None, str(e)