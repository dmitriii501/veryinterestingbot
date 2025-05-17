# main.py

import ai_module.nlu
from bot.handlers import handlers

user_message = "Кто завтра свободен в отделе маркетинга?"

# Получаем ответ от AI-модуля
text_response = ai_module.nlu.get_model_response(user_message)

# Парсим JSON
result = ai_module.nlu.parse_model_response(text_response)

print("Результат анализа запроса:")
print(result)

if __name__ == "__main__":
    handlers.start_bot()