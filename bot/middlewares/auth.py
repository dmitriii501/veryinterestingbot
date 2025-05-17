from cgitb import handler
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.loggers import event
from aiogram.types import Message, CallbackQuery, User, TelegramObject

class AuthMiddleware(BaseMiddleware):
    def __init__(self, allowed_ids: set[int]):
        super().__init__()
        self.allowed_ids = allowed_ids
        if not self.allowed_ids:
            print("ПРЕДУПРЕЖДЕНИЕ: AuthMiddleware инициализирован с пустым списком allowed_ids.")

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user: User | None = data.get('event_from_user')

        if user:
            if user.id not in self.allowed_ids:
                unauthorized_message = "🚫 Вы не авторизованы для использования этого бота."

                if isinstance(event, Message):
                    try:
                        await event.answer(unauthorized_message)
                    except Exception as e:
                        print(f"Ошибка отправки сообщения неавторизованному пользователю {user.id}: {e}")

                elif isinstance(event, CallbackQuery):
                    try:
                        await event.answer(unauthorized_message, show_alert=True)
                    except Exception as e:
                        print(f"Ошибка ответа на callback неавторизованному пользователю {user.id}: {e}")
                return

        else:
            print("AuthMiddleware: Не удалось определить пользователя из события. Доступ заблокирован.")
            return

        return await handler(event,data)