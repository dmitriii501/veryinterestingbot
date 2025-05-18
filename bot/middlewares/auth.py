import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
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
        # Get user from event data
        user: User | None = data.get('event_from_user')
        if not user:
            logging.error("Не удалось получить информацию о пользователе из события")
            return None

        if not self.allowed_ids or user.id in self.allowed_ids:
            return await handler(event, data)

        # User is not authorized
        unauthorized_message = "🚫 Вы не авторизованы для использования этого бота."
        logging.warning(f"Попытка доступа от неавторизованного пользователя: {user.id}")

        try:
            if isinstance(event, Message):
                await event.answer(unauthorized_message)
            elif isinstance(event, CallbackQuery):
                await event.answer(unauthorized_message, show_alert=True)
                if event.message:
                    await event.message.answer(unauthorized_message)
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения неавторизованному пользователю {user.id}: {e}")

        return None