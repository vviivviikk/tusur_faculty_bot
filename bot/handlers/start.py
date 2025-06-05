from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.keyboards.main_menu import get_main_menu

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я бот для подбора факультета ТУСУР 🎓\n\n"
        "Я помогу тебе:\n"
        "• Подобрать подходящий факультет на основе твоих интересов\n"
        "• Подать заявку на обучение\n"
        "• Отслеживать статус заявок\n\n"
        "Выбери действие в меню ниже:"
    )
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu()
    )


@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "🤖 Доступные команды:\n\n"
        "/start - Перезапустить бота\n"
        "/help - Показать эту справку\n"
        "Или используйте кнопки меню для навигации."
    )