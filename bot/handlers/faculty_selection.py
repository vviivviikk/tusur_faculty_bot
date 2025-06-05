from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import Config
from bot.keyboards.main_menu import get_faculty_inline_keyboard, get_main_menu
from bot.utils.ml_model import get_faculty_recommendation

from bot.utils.database import get_user_by_telegram_id, add_application

router = Router()

class FacultySelection(StatesGroup):
    waiting_for_favorite_subjects = State()
    waiting_for_disliked_subjects = State()
    waiting_for_exams = State()
    waiting_for_interests = State()
    waiting_for_dislikes = State()

@router.message(F.text == "🎓 Подобрать факультет")
async def start_faculty_selection(message: Message, state: FSMContext):
    await state.set_state(FacultySelection.waiting_for_favorite_subjects)
    text = (
        "Давай подберем тебе подходящий факультет! 🎯\n\n"
        "Сначала расскажи, какие предметы в школе тебе нравятся больше всего?\n"
        "Например: математика, физика, информатика, литература...\n\n"
        "Перечисли через запятую:\n\n"
        "💡 Для отмены анкеты используй команду /start"
    )
    await message.answer(text, reply_markup=ReplyKeyboardRemove())

@router.message(FacultySelection.waiting_for_favorite_subjects)
async def process_favorite_subjects(message: Message, state: FSMContext):
    await state.update_data(favorite_subjects=message.text)
    await state.set_state(FacultySelection.waiting_for_disliked_subjects)
    text = (
        "Отлично! 👍\n\n"
        "Теперь укажи предметы, которые тебе не очень нравятся:\n"
        "Перечисли через запятую:"
    )
    await message.answer(text)

@router.message(FacultySelection.waiting_for_disliked_subjects)
async def process_disliked_subjects(message: Message, state: FSMContext):
    await state.update_data(disliked_subjects=message.text)
    await state.set_state(FacultySelection.waiting_for_exams)
    text = (
        "Понятно! 📝\n\n"
        "Какие экзамены ты планируешь сдавать или уже сдал?\n"
        "Например: ЕГЭ по математике, физике, русскому языку...\n\n"
        "Перечисли через запятую:"
    )
    await message.answer(text)

@router.message(FacultySelection.waiting_for_exams)
async def process_exams(message: Message, state: FSMContext):
    await state.update_data(exams=message.text)
    await state.set_state(FacultySelection.waiting_for_interests)
    text = (
        "Хорошо! 📚\n\n"
        "Расскажи подробнее, что тебе интересно?\n"
        "Например: программирование, создание сайтов, работа с техникой, дизайн...\n\n"
        "Опиши своими словами:"
    )
    await message.answer(text)

@router.message(FacultySelection.waiting_for_interests)
async def process_interests(message: Message, state: FSMContext):
    await state.update_data(interests=message.text)
    await state.set_state(FacultySelection.waiting_for_dislikes)
    text = (
        "Замечательно! ✨\n\n"
        "И последний вопрос - что тебе точно неинтересно?\n"
        "Это поможет исключить неподходящие направления.\n\n"
        "Опиши своими словами:"
    )
    await message.answer(text)

@router.message(FacultySelection.waiting_for_dislikes)
async def process_dislikes_and_recommend(message: Message, state: FSMContext):
    await state.update_data(dislikes=message.text)
    user_data = await state.get_data()
    recommended_faculty = await get_faculty_recommendation(user_data)
    await state.clear()
    text = (
        f"🎯 Анализ завершен!\n\n"
        f"На основе твоих ответов рекомендую факультет:\n"
        f"**{recommended_faculty['name']}**\n\n"
        f"Почему именно он:\n{recommended_faculty['reason']}\n\n"
        f"Основные направления:\n{recommended_faculty['directions']}\n\n"
        "Выбери действие:"
    )
    keyboard = get_faculty_inline_keyboard(Config.FACULTIES)
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "submit_application")
async def submit_application_callback(callback: CallbackQuery, state: FSMContext):
    try:
        from bot.utils.database import get_user_by_telegram_id, create_or_update_user
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user:
            user = await create_or_update_user(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name
            )

        data = await state.get_data()
        faculty_code = data.get("selected_faculty_code")
        if not faculty_code:
            await callback.answer("Ошибка: факультет не выбран.", show_alert=True)
            return

        # --- Сохраняем заявку в отдельную таблицу:
        await add_application(user.id, faculty_code)

        await state.clear()
        faculty_name = Config.FACULTIES.get(faculty_code, faculty_code)
        await callback.message.edit_text(
            f"🎉 Ваша заявка на факультет <b>{faculty_name}</b> успешно подана!\n"
            "В ближайшее время с вами свяжутся сотрудники приемной комиссии.",
            reply_markup=None
        )
        # Добавляем главное меню:
        from bot.keyboards.main_menu import get_main_menu
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_main_menu()
        )
        await callback.answer("Заявка отправлена!", show_alert=True)
    except Exception as e:
        await callback.answer(f"Ошибка при подаче заявки: {str(e)}", show_alert=True)

@router.callback_query(F.data.startswith("faculty_"))
async def select_faculty_callback(callback: CallbackQuery, state: FSMContext):
    faculty_code = callback.data.split("_")[1]
    faculty_name = Config.FACULTIES.get(faculty_code, "Неизвестный факультет")
    text = (
        f"✅ **Выбран факультет:** {faculty_name}\n\n"
        "Хотите подать заявку на обучение на этом факультете?"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Да, подать заявку", callback_data="submit_application")],
        [InlineKeyboardButton(text="🔄 Выбрать другой факультет", callback_data="choose_another")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    await state.update_data(selected_faculty_code=faculty_code)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "choose_another")
async def choose_another_faculty(callback: CallbackQuery):
    keyboard = get_faculty_inline_keyboard(Config.FACULTIES)
    text = "Выберите другой факультет:"
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def return_to_main_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "Возвращаемся в главное меню:",
        reply_markup=get_main_menu()
    )
    await callback.answer()