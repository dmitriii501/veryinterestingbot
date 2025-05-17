import logging
from cgitb import handler
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.loggers import event
from aiogram.types import Message, CallbackQuery, User, TelegramObject

class AuthMiddleware(BaseMiddleware):
    def __init__(self, allowed_ids: set[int]):
        super().__init__()
        if isinstance(allowed_ids, str):
            try:
                self.allowed_ids = {int(uid.strip()) for uid in allowed_ids.split(',') if uid.strip().isdigit()}
            except ValueError:
                logging.warning(f"ОШИБКА: Некорректный формат allowed_ids: {allowed_ids}")
                self.allowed_ids = set()
        else:
            self.allowed_ids = set(allowed_ids)


        if not self.allowed_ids:
            logging.warning("ПРЕДУПРЕЖДЕНИЕ: AuthMiddleware инициализирован с пустым списком allowed_ids.")

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user: User | None = data.get('event_from_user')

        if user.id not in self.allowed_ids:
            unauthorized_message = "🚫 Вы не авторизованы для использования этого бота."
            logging.warning(f"Попытка доступа от неавторизованного пользователя: {user.id}")

            if isinstance(event, Message):
                try:
                    await event.reply(unauthorized_message)
                except Exception as e:
                    logging.warning(f"Ошибка отправки сообщения неавторизованному пользователю {user.id}: {e}")

                    try:
                        await event.answer(unauthorized_message)
                    except Exception as e2:
                        logging.warning(f"Альтернативная отправка тоже не удалась: {e2}")

            elif isinstance(event, CallbackQuery):
                try:

                    await event.answer(unauthorized_message, show_alert=True)
                    if event.message:
                        await event.message.reply(unauthorized_message)

                except Exception as e:
                    logging.warning(f"Ошибка ответа на callback неавторизованному пользователю {user.id}: {e}")

            return None

        return await handler(event,data)