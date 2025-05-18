import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple

from supabase import Client, create_client, PostgrestAPIResponse

logger = logging.getLogger(__name__)


async def execute_supabase_query(
        supabase_client: Client,
        table_name: str,
        select_columns: str = "*",
        filters: Optional[List[Dict[str, Any]]] = None,
        order_by: Optional[Tuple[str, str]] = None,
        limit: Optional[int] = None
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """
    Выполняет запрос к базе данных Supabase с заданными параметрами.

    Args:
        supabase_client: Клиент Supabase
        table_name: Имя таблицы
        select_columns: Строка с перечислением колонок для выборки
        filters: Список словарей с фильтрами {'column': 'имя_колонки', 'operator': 'eq|neq|gt|...', 'value': значение}
        order_by: Кортеж (имя_колонки, 'asc'|'desc') для сортировки
        limit: Ограничение количества возвращаемых записей

    Returns:
        Кортеж (данные, ошибка) - если ошибки нет, то второй элемент None
    """
    # Проверка наличия клиента Supabase
    if not supabase_client:
        logger.error("Клиент Supabase не был предоставлен.")
        return None, "Клиент Supabase не инициализирован"

    try:
        # Инициализация запроса
        query = supabase_client.table(table_name).select(select_columns)

        # Применение фильтров
        if filters:
            for f in filters:
                col = f.get('column')
                op = f.get('operator')
                val = f.get('value')

                if not all([col, op]):
                    logger.warning(f"Неполный фильтр пропущен: {f}")
                    continue

                # Проверка и применение оператора фильтрации
                if op == 'eq':
                    query = query.eq(col, val)
                elif op == 'neq':
                    query = query.neq(col, val)
                elif op == 'gt':
                    query = query.gt(col, val)
                elif op == 'lt':
                    query = query.lt(col, val)
                elif op == 'gte':
                    query = query.gte(col, val)
                elif op == 'lte':
                    query = query.lte(col, val)
                elif op == 'like':
                    query = query.like(col, f'%{val}%')
                elif op == 'ilike':
                    query = query.ilike(col, f'%{val}%')
                elif op == 'in':
                    # Обработка списков для оператора 'in'
                    if isinstance(val, str):
                        val_list = [item.strip() for item in val.split(',')]
                        # Пытаемся преобразовать строковые числа в int
                        try:
                            val_list = [int(item) if item.isdigit() else item for item in val_list]
                        except ValueError:
                            pass
                        query = query.in_(col, val_list)
                    elif isinstance(val, list):
                        query = query.in_(col, val)
                    else:
                        logger.warning(
                            f"Для оператора 'in' значение должно быть списком или строкой через запятую: {val}")
                        continue
                else:
                    logger.warning(f"Неизвестный оператор фильтрации '{op}' для таблицы '{table_name}'.")

        # Применение сортировки
        if order_by:
            col_name, direction = order_by  # Исправлена ошибка: было dictionary вместо direction
            is_ascending = direction.lower() == 'asc'
            query = query.order(col_name, ascending=is_ascending, nulls_first=False)

        # Применение лимита
        if limit is not None:
            query = query.limit(limit)

        logger.debug(
            f"Выполнение запроса к Supabase: Таблица='{table_name}', Колонки='{select_columns}', "
            f"Фильтры={filters}, Сортировка={order_by}, Лимит={limit}")

        # Выполнение запроса асинхронно
        response: PostgrestAPIResponse = await asyncio.to_thread(query.execute)

        # Обработка результатов запроса
        if response.data is not None:
            logger.debug(f"Получен ответ от Supabase, количество записей: {len(response.data)}")
            return response.data, None
        else:
            if response.error:
                logger.error(
                    f"Ошибка от Supabase API: код={response.error.code}, "
                    f"сообщение='{response.error.message}', детали='{response.error.details}', "
                    f"хинт='{response.error.hint}'")
                return None, f"Ошибка API: {response.error.message}"

            logger.warning(
                f"Запрос к Supabase для таблицы {table_name} вернул None в data без явной ошибки API. "
                f"Ответ: {response}")
            return [], None  # Возвращаем пустой список, если нет данных, но и нет ошибки

    except Exception as e:
        logger.error(f"Общая ошибка при запросе к Supabase (таблица {table_name}): {e}", exc_info=True)
        return None, str(e)