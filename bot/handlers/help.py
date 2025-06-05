from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message):
    text = (
        "🤖 Справка по использованию бота:\n\n"
        "🎓 Подобрать факультет - пройти анкету для получения рекомендации\n"
        "📝 Мои заявки - посмотреть поданные заявки\n"
        "👤 Профиль - информация о вашем аккаунте\n"
        "ℹ️ Помощь - эта справка\n\n"
        "Для отмены любого действия используйте команду /start\n\n"
    )
    await message.answer(text)