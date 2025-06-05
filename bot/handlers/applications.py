from aiogram import Router, F
from aiogram.types import Message
from bot.utils.database import get_user_by_telegram_id, create_or_update_user

from bot.utils.database import get_user_by_telegram_id, get_applications_by_user_id
from bot.config import Config

router = Router()


@router.message(F.text == "📝 Мои заявки")
async def show_applications(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала завершите регистрацию!")
        return
    applications = await get_applications_by_user_id(user.id)
    if not applications:
        await message.answer("Пока нет заявок.")
        return

    text = "📑 Ваши заявки:\n\n"
    for app in applications:
        faculty_name = Config.FACULTIES.get(app.faculty_code, app.faculty_code)
        text += f"• {faculty_name} ({app.status})\n"
    await message.answer(text)