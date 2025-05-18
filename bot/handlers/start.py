from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router(name="start")


@router.message(Command("start"))
async def start_command(message: Message):
    welcome_text = (
        "👋 Привет! Я корпоративный бот-ассистент.\n\n"
        "🔍 Я помогу вам:\n"
        "- Найти информацию о сотрудниках\n"
        "- Управлять мероприятиями\n"
        "- Отслеживать задачи\n\n"
        "💡 Основные команды:\n"
        "/nlu - Поиск информации\n"
        "/help - Подробная справка\n\n"
        "✨ Вы можете написать мне свой вопрос, и я постараюсь помочь!"
    )
    
    await message.answer(welcome_text)