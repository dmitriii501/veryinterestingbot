from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from ..Keyboards import get_main_menu_keyboard, get_help_keyboard

router = Router(name="Помощник")

help_text = ("Zaglushka@gmail.com")

@router.message(Command("help"))
async def help_command(message: Message):
    help_text = (
        "📚 Справка по командам и возможностям:\n\n"
        "🔍 Поиск информации:\n"
        "/search - Поиск по базе данных\n"
        "/query - Задать вопрос в свободной форме\n\n"
        "📅 Мероприятия:\n"
        "- 'Создай встречу [название] [дата] [время]'\n"
        "- 'Какие мероприятия на этой неделе?'\n\n"
        "📋 Задачи:\n"
        "- 'Создай задачу [название] до [дата]'\n"
        "- 'Покажи мои задачи на сегодня'\n\n"
        "👥 Сотрудники:\n"
        "- 'Найди [имя] из [отдел]'\n"
        "- 'Кто работает над проектом [название]?'\n\n"
        "💡 Вы можете задавать вопросы в свободной форме,\n"
        "я постараюсь понять ваш запрос и найти нужную информацию!"
    )
    
    await message.answer(help_text)

@router.message(F.text == "ℹ️ Помощь")
async def text_help_button(message: Message):
    await message.answer(help_text)
    reply_markup=get_help_keyboard()