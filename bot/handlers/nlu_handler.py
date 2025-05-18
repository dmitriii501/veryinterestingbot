from aiogram import Router, types
from aiogram.filters import Command
from aiogram import Bot, Dispatcher  # Импортируем Bot

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
    
    # Системный промпт для NLU парсера
    system_prompt = (
        "Ты — AI-парсер запросов в корпоративном приложении. "
        "Пользователь пишет запрос в свободной форме. Твоя задача — извлечь только intent (намерение) "
        "и entities (сущности), которые явно указаны в тексте. Не отвечай на вопрос, не выдумывай данные, "
        "не интерпретируй неявные фразы. Дата должна быть только в формате дд.мм.гггг. "
        "Если дата указана иначе (например, 'завтра'), не добавляй сущность date. "
        "Если сущность не указана — не включай её в JSON. "
        "Ответ строго в формате JSON.\n\n"
        "Возможные интенты:\n"
        "- find_employee: Поиск сотрудника\n"
        "- event_info: Информация о мероприятиях\n"
        "- birthday_info: Информация о днях рождения\n"
        "- task_info: Информация о задачах\n"
        "- availability: Проверка доступности сотрудника\n"
        "- lunch_game_invite: Поиск коллег по интересам для обеда/игр\n"
        "- general_question: Общий вопрос\n"
        "- unknown: Неопределенный запрос\n\n"
        "Возможные сущности:\n"
        "- employee_name: Имя сотрудника\n"
        "- department: Отдел\n"
        "- project: Проект\n"
        "- date: Дата (только в формате дд.мм.гггг)\n"
        "- event_type: Тип мероприятия\n"
        "- task_keyword: Ключевое слово, связанное с задачей\n"
        "- location: Место\n\n"
        "Примеры запросов и ожидаемые ответы:\n"
        '1. Запрос: "Кто из разработки работает 20.05.2025?"\n'
        ' Ответ:\n'
        ' {\n'
        ' "intent": "availability",\n'
        ' "entities": {\n'
        ' "department": "разработки",\n'
        ' "date": "20.05.2025"\n'
        ' }\n'
        ' }\n\n'
        '2. Запрос: "Какие задачи у Ивана на завтра?"\n'
        ' Ответ:\n'
        ' {\n'
        ' "intent": "task_info",\n'
        ' "entities": {\n'
        ' "employee_name": "Ивана",\n'
        ' "task_keyword": "задачи"\n'
        ' }\n'
        ' }\n\n'
        '3. Запрос: "Когда день рождения у Марии?"\n'
        ' Ответ:\n'
        ' {\n'
        ' "intent": "birthday_info",\n'
        ' "entities": {\n'
        ' "employee_name": "Марии"\n'
        ' }\n'
        ' }\n\n'
    )

    # Вызываем асинхронную функцию process_user_query из ai_module.nlu
    response = await process_user_query(user_message, system_prompt)
    
    if response:
        await message.reply(response)  # Отправляем ответ пользователю
    else:
        await message.reply(
            "Извините, не удалось обработать ваш запрос. Попробуйте еще раз."
        )