import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot.utils.database import engine
from backend.models.base import Base
from bot.config import Config

# Импорты роутеров - импортируем роутеры напрямую
from bot.handlers.start import router as start_router
from bot.handlers.faculty_selection import router as faculty_router
from bot.handlers.applications import router as applications_router
from bot.handlers.profile import router as profile_router
from bot.handlers.help import router as help_router
from bot.handlers.common_handlers import router as common_router

async def on_startup():
    """Инициализация при старте бота"""
    # СОЗДАЕМ ВСЕ ТАБЛИЦЫ в базе! (Это обязательно)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("✅ База данных готова!")
    
    # Инициализируем ML-модель
    try:
        from bot.utils.ml_model import ensure_model_initialized
        await ensure_model_initialized()
        logging.info("✅ ML-модель инициализирована!")
    except Exception as e:
        logging.warning(f"⚠️ ML-модель не инициализирована: {e}")
        logging.warning("Бот будет работать с резервным алгоритмом рекомендаций")

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if not Config.BOT_TOKEN:
        logging.error("BOT_TOKEN не задан в переменных окружения.")
        return

    await on_startup()

    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # ИСПРАВЛЕННОЕ подключение роутеров
    dp.include_router(start_router)
    dp.include_router(faculty_router)
    dp.include_router(applications_router)
    dp.include_router(profile_router)
    dp.include_router(help_router)
    dp.include_router(common_router)
    
    logging.info("🚀 Бот запущен с ML-моделью.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())