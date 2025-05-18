import asyncio
import logging
from typing import Optional
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from supabase import create_client, Client

from bot.config import app_settings

# Импорты обработчиков
from bot.handlers import start
from bot.handlers import help as help_command
from bot.handlers import ai_query as ai_query_handler  # Переименовано для ясности
from bot.handlers import employees_handler
from bot.handlers import nlu_handler  # Оригинальный обработчик NLU
from bot.handlers import ai_intent_handler  # Новый обработчик AI интентов

from bot.middlewares.auth import AuthMiddleware


def convert_date_format(dmy_date_str: str) -> Optional[str]:
    """
    Преобразует дату из формата ДД.ММ.ГГГГ в ГГГГ-ММ-ДД

    Args:
        dmy_date_str: Строка с датой в формате ДД.ММ.ГГГГ

    Returns:
        Строка с датой в формате ГГГГ-ММ-ДД или None в случае ошибки
    """
    if not dmy_date_str:
        return None
    try:
        # Преобразуем из дд.мм.гггг в объект datetime
        dt_obj = datetime.strptime(dmy_date_str, "%d.%m.%Y")
        # Форматируем в гггг-мм-дд
        return dt_obj.strftime("%Y-%m-%d")
    except ValueError:
        logging.warning(f"Некорректный формат даты: {dmy_date_str}. Ожидался дд.мм.гггг")
        return None


def register_router(dp: Dispatcher, module, module_name: str) -> bool:
    """
    Регистрирует роутер из модуля в диспетчере

    Args:
        dp: Экземпляр диспетчера
        module: Импортированный модуль с роутером
        module_name: Имя модуля для логирования

    Returns:
        True если регистрация успешна, иначе False
    """
    if hasattr(module, "router"):
        dp.include_router(module.router)
        logging.info(f"Роутер '{module.router.name or module_name}' зарегистрирован.")
        return True
    else:
        logging.error(f"Роутер из {module_name} не найден или не имеет атрибута 'router'.")
        return False


async def setup_supabase(bot: Bot) -> None:
    """
    Настраивает подключение к Supabase и добавляет клиент в объект бота

    Args:
        bot: Экземпляр бота
    """
    try:
        if not app_settings.SUPABASE_URL or not app_settings.SUPABASE_KEY:
            logging.error("SUPABASE_URL и/или SUPABASE_KEY не установлены в конфигурации.")
            bot.supabase_client = None
        else:
            supabase_client_instance: Client = create_client(
                app_settings.SUPABASE_URL, app_settings.SUPABASE_KEY
            )
            logging.info("Успешно подключились к Supabase!")
            bot.supabase_client = supabase_client_instance
    except Exception as e:
        logging.error(f"Ошибка подключения к Supabase: {e}", exc_info=True)
        bot.supabase_client = None


async def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s: %(message)s",
    )
    logging.info("Запуск бота...")

    # Инициализация бота и диспетчера
    storage = MemoryStorage()
    bot = Bot(
        token=app_settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=storage)

    # Настройка авторизации
    if app_settings.ALLOWED_USER_IDS:
        logging.info(
            f"Авторизация по ID включена. Разрешенные ID: {app_settings.ALLOWED_USER_IDS}"
        )
        dp.update.outer_middleware.register(
            AuthMiddleware(allowed_ids=app_settings.ALLOWED_USER_IDS)
        )
    else:
        logging.warning(
            "ALLOWED_USER_IDS не настроен или пуст. Авторизация по ID отключена."
        )

    # Настройка Supabase
    await setup_supabase(bot)

    # Регистрация обработчиков
    logging.info("Регистрация хендлеров...")

    # Список модулей с роутерами для регистрации
    router_modules = [
        (start, "bot.handlers.start"),
        (help_command, "bot.handlers.help"),
        (ai_query_handler, "bot.handlers.ai_query"),
        (employees_handler, "bot.handlers.employees_handler"),
        (nlu_handler, "bot.handlers.nlu_handler"),  # Оригинальный NLU обработчик
        (ai_intent_handler, "bot.handlers.ai_intent_handler")  # Дополнительный новый обработчик AI интентов
    ]

    # Регистрация всех роутеров
    for module, module_name in router_modules:
        register_router(dp, module, module_name)

    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Начинаем поллинг...")

    try:
        await dp.start_polling(bot)
    finally:
        logging.info("Остановка бота...")
        await bot.session.close()
        logging.info("Сессия бота закрыта.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен вручную.")
    except Exception as e:
        logging.exception(f"Критическая ошибка при запуске/работе бота: {e}")