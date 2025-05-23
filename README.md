# Corporate Communication Bot

Интеллектуальный корпоративный бот для управления коммуникациями и задачами с использованием двухэтапной AI-обработки.

## Возможности

- 🤖 Двухэтапная AI-обработка запросов:
  - NLU (Natural Language Understanding) для определения намерений и сущностей
  - Генерация контекстных ответов на основе данных из Supabase
- 👥 Управление сотрудниками:
  - Поиск по отделам и проектам
  - Проверка доступности

## Архитектура

```
bot/
├── ai_module/          # Модули AI-обработки
│   ├── nlu.py         # NLU процессор
│   └── response_generator.py  # Генератор ответов
├── handlers/           # Обработчики сообщений
├── middlewares/        # Middleware компоненты
├── models/            # Модели данных
├── utils/             # Вспомогательные функции
└── config.py          # Конфигурация

```

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd veryinterestingbot
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` в корневой директории:
```env
# Telegram
BOT_TOKEN=your_bot_token
ALLOWED_USER_IDS=123456789,987654321

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# AI
AI_API_KEY=your_nscale_api_key
```

## Запуск

```bash
python main.py
```

## Разработка

### Структура обработки сообщений

1. Входящее сообщение → NLU процессор:
   - Извлечение намерения (intent)
   - Извлечение сущностей (entities)

2. NLU результат → Генератор ответов:
   - Запрос данных из Supabase
   - Генерация контекстного ответа

### Добавление новых возможностей

1. Определите новый intent в `ai_module/nlu.py`
2. Добавьте обработку в `ai_module/response_generator.py`
3. При необходимости создайте новые модели в Supabase

## Тестирование

```bash
# Запуск всех тестов
python -m pytest

# Запуск конкретного модуля
python -m pytest tests/test_nlu.py
```

## Логирование

Логи сохраняются в:
- `bot.log` - основной лог файл
- Консоль - для отладки

## Лицензия

MIT
ПРИМЕР РАБОТЫ МОЖНО УВИДЕТЬ В ЭТОМ ТГК! - https://t.me/resultofwork