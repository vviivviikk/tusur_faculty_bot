from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.keyboards.main_menu import get_main_menu

router = Router()


@router.message(Command("cancel"))
@router.message(F.text.in_(["❌ Отменить", "🏠 Главное меню", "📝 Мои заявки", "👤 Профиль", "ℹ️ Помощь"]))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(
            "Действие отменено. Возвращаемся в главное меню.",
            reply_markup=get_main_menu()
        )
    if message.text == "👤 Профиль":
        from bot.handlers.profile import show_profile
        await show_profile(message)
    elif message.text == "📝 Мои заявки":
        from bot.handlers.applications import show_applications
        await show_applications(message)
    elif message.text == "ℹ️ Помощь":
        from bot.handlers.help import show_help
        await show_help(message)
    else:
        await message.answer(
            "Выберите действие:",
            reply_markup=get_main_menu()
        )