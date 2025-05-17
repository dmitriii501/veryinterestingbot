from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="Команда старт")

@router.message(CommandStart())
async def cmd_start(message: Message):

    user_name = message.from_user.full_name
    user_id = message.from_user.id


    greeting_text = (
        f"👋 Привет, {user_name}!\n\n"
        "Я ваш корпоративный AI-ассистент. Готов помочь вам с поиском информации "
        "о сотрудниках, мероприятиях и задачах.\n\n"
        "Просто задайте мне вопрос в свободной форме, например:\n"
        " • 'Какие мероприятия запланированы на следующей неделе?'\n"
        " • 'Найди контактные данные Ивана Петрова из отдела маркетинга.'\n"
        " • 'Какие у меня задачи на сегодня?'\n\n"
        f"Для получения списка команд введите /help."
    )

    await message.answer(greeting_text)