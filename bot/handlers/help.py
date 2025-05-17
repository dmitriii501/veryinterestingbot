from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from ..Keyboards import get_main_menu_keyboard, get_help_keyboard

router = Router(name="Помощник")

help_text = ("Zaglushka@gmail.com")

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(help_text)
    reply_markup=get_help_keyboard()

@router.message(F.text == "ℹ️ Помощь")
async def text_help_button(message: Message):
    await message.answer(help_text)
    reply_markup=get_help_keyboard()