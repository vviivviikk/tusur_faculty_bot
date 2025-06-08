from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.keyboards.main_menu import get_main_menu
from bot.utils.database import create_or_update_user

router = Router()

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    await state.clear()

    user = await create_or_update_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    welcome_text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Добро пожаловать в бот подбора факультета ТУСУР! 🎓\n\n"
        "Я помогу тебе:\n"
        "🔹 Подобрать подходящий факультет на основе твоих интересов\n"
        "🔹 Подать заявку на поступление\n"
        "🔹 Отслеживать статус заявок\n\n"
        "Выбери действие в меню ниже:"
    )
    
    await message.answer(welcome_text, reply_markup=get_main_menu())
