import os
import sys
import requests
from datetime import datetime

print("🔧 ДИАГНОСТИКА КОНФИГУРАЦИИ TELEGRAM-БОТА")
print("=" * 50)

# Проверка файла .env
print("🔍 Проверка файла .env...")
env_path = '.env'

if not os.path.exists(env_path):
    print("❌ Файл .env не найден в корне проекта!")
    print("Создайте файл .env со следующим содержимым:")
    print("BOT_TOKEN=ваш_токен_от_BotFather")
    print("DEBUG=True")
else:
    print("✅ Файл .env найден")

    # Читаем содержимое
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            env_content = f.read()

        if 'BOT_TOKEN=' in env_content:
            print("✅ Переменная BOT_TOKEN найдена в файле")

            # Извлекаем токен
            for line in env_content.splitlines():
                if line.startswith('BOT_TOKEN='):
                    token = line[10:].strip()
                    if token and token != 'your_bot_token_here' and len(token) > 20:
                        print(f"✅ Токен установлен (длина: {len(token)} символов)")
                        print(f"Начало токена: {token[:10]}...")

                        if ':' in token:
                            print("✅ Формат токена выглядит корректно")
                        else:
                            print("❌ Формат токена некорректен! Должен содержать ':'!")
                    else:
                        print("❌ Токен не установлен или содержит заглушку")
                    break
        else:
            print("❌ Переменная BOT_TOKEN не найдена в файле .env!")
    except Exception as e:
        print(f"❌ Ошибка при чтении .env файла: {e}")

print("\n🔍 Проверка загрузки переменных окружения...")
# Проверяем python-dotenv
try:
    from dotenv import load_dotenv

    print("✅ Библиотека python-dotenv установлена")

    # Пробуем загрузить с dotenv
    load_dotenv()
    token_from_env = os.getenv('BOT_TOKEN')
    if token_from_env:
        print("✅ Токен успешно загружен через os.getenv()")
    else:
        print("❌ Не удалось загрузить токен через os.getenv()")

except ImportError:
    print("❌ Библиотека python-dotenv не установлена")
    print("Установите ее командой: pip install python-dotenv")

print("\n🔍 Проверка структуры проекта...")
# Проверяем структуру проекта
required_files = [
    'main.py',
    'requirements.txt',
    'bot/config.py',
    'bot/handlers/start.py',
    'bot/__init__.py',
    'bot/handlers/__init__.py',
]

print("Обязательные файлы:")
for file in required_files:
    if os.path.exists(file):
        print(f"✅ {file}")
    else:
        print(f"❌ {file} - не найден")

print("\n🔍 Проверка импорта модулей...")
# Проверяем необходимые модули
required_modules = ['aiogram', 'dotenv', 'asyncio', 'requests']
for module in required_modules:
    try:
        if module == 'dotenv':
            import dotenv
        elif module == 'requests':
            import requests
        elif module == 'asyncio':
            import asyncio
        elif module == 'aiogram':
            import aiogram
        print(f"✅ {module} - установлен")
    except ImportError as e:
        print(f"❌ {module} - НЕ УСТАНОВЛЕН: {e}")

print("\n🔍 Проверка конфигурации бота...")
# Проверяем конфигурацию бота
try:
    from bot.config import Config

    print("✅ Модуль Config импортирован успешно")

    if hasattr(Config, 'BOT_TOKEN'):
        if Config.BOT_TOKEN:
            print(f"✅ Config.BOT_TOKEN установлен (длина: {len(Config.BOT_TOKEN)})")
        else:
            print("❌ Config.BOT_TOKEN равен None")
    else:
        print("❌ В классе Config нет атрибута BOT_TOKEN")
except Exception as e:
    print(f"❌ Ошибка при импорте Config: {e}")

print("\n🔍 Проверка токена через Telegram API...")
# Тестируем токен через Telegram API
token_to_check = None

try:
    token_to_check = os.getenv('BOT_TOKEN')
    if not token_to_check:
        from bot.config import Config

        token_to_check = Config.BOT_TOKEN
except:
    pass

if not token_to_check:
    print("❌ Не удалось получить токен ни из переменных окружения, ни из Config")
else:
    try:
        url = f"https://api.telegram.org/bot{token_to_check}/getMe"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and data.get('ok'):
            print("✅ Токен прошел проверку через Telegram API")
            bot_info = data['result']
            print(f"Имя бота: {bot_info.get('first_name')}")
            print(f"Username: @{bot_info.get('username')}")
            print(f"ID бота: {bot_info.get('id')}")
        else:
            print(f"❌ Ошибка авторизации ({response.status_code})")
            print(f"Ответ API: {data.get('description', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Ошибка при проверке токена через API: {e}")

# Итоговый отчет
print("\n📊 ИТОГОВЫЙ ОТЧЕТ:")
print(f"Файл .env: {'✅' if os.path.exists('.env') else '❌'}")

dotenv_available = False
try:
    import dotenv

    dotenv_available = True
except ImportError:
    pass
print(f"Загрузка dotenv: {'✅' if dotenv_available else '❌'}")

structure_ok = all(os.path.exists(f) for f in required_files)
print(f"Структура проекта: {'✅' if structure_ok else '❌'}")

modules_ok = True
for module in required_modules:
    try:
        if module == 'dotenv':
            import dotenv
        elif module == 'requests':
            import requests
        elif module == 'asyncio':
            import asyncio
        elif module == 'aiogram':
            import aiogram
    except ImportError:
        modules_ok = False
        break
print(f"Импорт модулей: {'✅' if modules_ok else '❌'}")

config_ok = False
try:
    from bot.config import Config

    if Config.BOT_TOKEN:
        config_ok = True
except:
    pass
print(f"Конфигурация бота: {'✅' if config_ok else '❌'}")

has_valid_token = False
if token_to_check:
    try:
        url = f"https://api.telegram.org/bot{token_to_check}/getMe"
        response = requests.get(url)
        if response.status_code == 200 and response.json().get('ok'):
            has_valid_token = True
    except:
        pass
print(f"Telegram API: {'✅' if has_valid_token else '❌'}")

# Заключение
if all([
    os.path.exists('.env'),
    dotenv_available,
    structure_ok,
    modules_ok,
    config_ok,
    has_valid_token
]):
    print("\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Бот должен запускаться без ошибок.")
else:
    print("\n⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ. Исправьте их перед запуском бота.")

print("\n" + "=" * 50)
print("Проверка завершена")