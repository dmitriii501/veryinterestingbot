# main.py

#import ai_module.nlu

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from bot.config import app_settings

from bot.handlers import start
from bot.handlers import help as help_command
from bot.handlers import ai_query as ai_query_handler

from bot.middlewares.auth import AuthMiddleware

async  def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s: %(message)s",
    )
    logging.info("Запуск бота...")

    storage = MemoryStorage()
    default_props = DefaultBotProperties(parse_mode="HTML")
    bot = Bot(token=app_settings.BOT_TOKEN, default=default_props)
    dp = Dispatcher(storage=storage)

    if app_settings.ALLOWED_USER_IDS:

        logging.info(f"Авторизация по ID включена. Разрешенные ID: {app_settings.ALLOWED_USER_IDS}")

        dp.update.outer_middleware.register(AuthMiddleware(allowed_ids=app_settings.ALLOWED_USER_IDS))

    else:

        logging.warning("ALLOWED_USER_IDS не настроен или пуст. Авторизация по ID отключена.")

    logging.info("Регистрация хендлеров...")
    if hasattr(start, 'router'):
        dp.include_router(start.router)
        logging.info(f"Роутер '{start.router.name or 'start'}' зарегистрирован.")
    else:
        logging.error("Роутер из bot.handlers.start не найден или не имеет атрибута 'router'.")

    if hasattr(help_command, 'router'):
        dp.include_router(help_command.router)
        logging.info(f"Роутер '{help_command.router.name or 'help_command'}' зарегистрирован.")
    else:
        logging.error("Роутер из bot.handlers.help не найден или не имеет атрибута 'router'.")

    if hasattr(ai_query_handler, 'router'):
        dp.include_router(ai_query_handler.router)
        logging.info(f"Роутер '{ai_query_handler.router.name or 'ai_query_handler'}' зарегистрирован.")
    else:
        logging.error("Роутер из bot.handlers.ai_query не найден или не имеет атрибута 'router'.")

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Начинаем поллинг...")

    try:
        await dp.start_polling(bot)
    finally:
        logging.info("Остановка бота...")
        await bot.session.close()
        logging.info("Сессия бота закрыта.")


user_message = "Кто завтра свободен в отделе маркетинга?"

# Получаем ответ от AI-модуля
#text_response = ai_module.nlu.get_model_response(user_message)

# Парсим JSON
#result = ai_module.nlu.parse_model_response(text_response)

#print("Результат анализа запроса:")
#print(result)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен вручную.")
    except Exception as e:
        logging.exception(f"Критическая ошибка при запуске/работе бота: {e}")