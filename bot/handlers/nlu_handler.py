# bot\handlers\nlu_handler.py
from aiogram import Router, types
from aiogram.filters import Command
from aiogram import Bot, Dispatcher #Импортируем Bot

# Предполагается, что process_user_query находится в ai_module/nlu.py
from ai_module.nlu import process_user_query  # Импортируем функцию process_user_query
#from bot.keyboards.inline import *
#from bot.utils.utils import *

router = Router()
#dp = Dispatcher(bot) #Удаляем Bot из инициализации
#Предполагается, что объект bot уже создан и передан в этот модуль.
#Если это не так, вам нужно будет импортировать его и использовать здесь.

@router.message(Command("nlu"))  # Пример команды для запуска обработки NLU
async def nlu_command_handler(message: types.Message):
    """
    Этот обработчик будет вызываться, когда пользователь отправляет команду /nlu.
    Он получает текст сообщения пользователя и отправляет его на обработку в NLU модуль.
    """
    user_message = message.text
    # Системный промпт можно определить здесь или загрузить из конфигурации
    system_prompt = "Отвечай как полезный ассистент."  # Пример системного промпта

    # Вызываем асинхронную функцию process_user_query из ai_module.nlu
    response = await process_user_query(user_message, system_prompt)

    if response:
        await message.reply(response)  # Отправляем ответ пользователю
    else:
        await message.reply(
            "Извините, не удалось обработать ваш запрос. Попробуйте еще раз."
        )
