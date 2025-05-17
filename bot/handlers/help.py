from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="Помощник")

@router.message(Command("help"))
async def cmd_help(message: Message):

    help_text = ("Zaglushka@gmail.com")

    await message.answer(help_text)