from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
        kb = [
            [KeyboardButton(text="❓ Задать вопрос AI")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ]
        keyboard = ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder="Выберите действие или введите вопрос...",
            selective=True
        )
        return keyboard

def get_help_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="⬅️ Назад в меню")]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard