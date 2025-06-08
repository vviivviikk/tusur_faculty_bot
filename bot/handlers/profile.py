from aiogram import Router, F
from aiogram.types import Message
from bot.utils.database import get_user_by_telegram_id, get_applications_by_user_id
from bot.config import Config

router = Router()

@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Профиль не найден. Сначала завершите регистрацию.")
        return

    applications = await get_applications_by_user_id(user.id)
    faculty_names = []
    for app in applications:
        faculty_name = Config.FACULTIES.get(app.faculty_code, app.faculty_code)
        faculty_names.append(faculty_name)

    faculties_text = ", ".join(faculty_names) if faculty_names else "-"

    text = (
        f"👤 Ваш профиль:\n\n"
        f"Имя: {user.first_name or '-'}\n"
        f"Фамилия: {user.last_name or '-'}\n"
        f"Телефон: {user.phone or '-'}\n"
        f"E-mail: {user.email or '-'}\n"
        f"Роль: {user.role or '-'}\n"
        f"Факультет(ы): {faculties_text}"
    )
    await message.answer(text)