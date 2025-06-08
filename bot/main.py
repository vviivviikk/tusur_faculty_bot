import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot.utils.database import engine
from backend.models.base import Base
from bot.config import Config
from bot.utils.database import engine, Base

from bot.handlers import (
    start,
    faculty_selection,
    applications,
    profile,
    help,
    common_handlers
)

async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("✅ База данных готова!")

    from bot.utils.ml_model import initialize_ml_model
    await initialize_ml_model()

async def main():
    logging.basicConfig(level=logging.INFO)
    if not Config.BOT_TOKEN:
        logging.error("BOT_TOKEN не задан.")
        return

    await on_startup()

    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(start)
    dp.include_router(faculty_selection)
    dp.include_router(applications)
    dp.include_router(profile)
    dp.include_router(help)
    dp.include_router(common_handlers)
    logging.info("🚀 Бот запущен.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
