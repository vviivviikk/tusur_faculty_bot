from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import Config
from bot.keyboards.main_menu import get_faculty_inline_keyboard, get_main_menu
from bot.keyboards.subjects import get_subjects_keyboard, SUBJECTS_LIST
from bot.utils.ml_model import get_faculty_recommendation

from bot.utils.database import get_user_by_telegram_id, add_application, create_or_update_user, async_session

router = Router()

class FacultySelection(StatesGroup):
    waiting_for_favorite_subjects = State()
    waiting_for_disliked_subjects = State()
    waiting_for_exams = State()
    waiting_for_interests = State()
    waiting_for_dislikes = State()
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_email = State()
    waiting_for_phone = State()

# Шаг 1: любимые предметы ― КНОПКИ
@router.message(F.text == "🎓 Подобрать факультет")
async def start_faculty_selection(message: Message, state: FSMContext):
    await state.set_state(FacultySelection.waiting_for_favorite_subjects)
    await state.update_data(favorite_subjects=[])
    text = (
        "Давай подберем тебе подходящий факультет! 🎯\n\n"
        "Выбери предметы, которые тебе нравятся (можно несколько). После выбора нажми «✅ Готово»."
    )
    await message.answer(text, reply_markup=get_subjects_keyboard())

@router.message(FacultySelection.waiting_for_favorite_subjects)
async def process_favorite_subjects(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    selected = data.get("favorite_subjects", [])
    if text == "✅ Готово":
        if not selected:
            await message.answer("Выбери хотя бы один любимый предмет.", reply_markup=get_subjects_keyboard())
            return
        await state.set_state(FacultySelection.waiting_for_disliked_subjects)
        await state.update_data(disliked_subjects=[])
        await message.answer(
            "Теперь выбери предметы, которые тебе не нравятся (можно несколько). После выбора нажми «✅ Готово».",
            reply_markup=get_subjects_keyboard()
        )
    elif text in SUBJECTS_LIST:
        if text not in selected:
            selected.append(text)
        await state.update_data(favorite_subjects=selected)
        await message.answer(
            f"Добавлено: {text}\nМожешь выбрать ещё, потом нажать «✅ Готово».",
            reply_markup=get_subjects_keyboard()
        )
    else:
        await message.answer("Пожалуйста, выбирай только из предложенных кнопок.", reply_markup=get_subjects_keyboard())

# Шаг 2: нелюбимые предметы ― КНОПКИ
@router.message(FacultySelection.waiting_for_disliked_subjects)
async def process_disliked_subjects(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    selected = data.get("disliked_subjects", [])
    if text == "✅ Готово":
        await state.set_state(FacultySelection.waiting_for_exams)
        await message.answer(
            "Какие экзамены ты планируешь сдавать или уже сдал?\nНапример: ЕГЭ по математике, русскому, физике и т.д.\n\nПеречисли через запятую:",
            reply_markup=ReplyKeyboardRemove()
        )
    elif text in SUBJECTS_LIST:
        if text not in selected:
            selected.append(text)
        await state.update_data(disliked_subjects=selected)
        await message.answer(
            f"Добавлено: {text}\nМожешь выбрать ещё, потом нажать «✅ Готово».",
            reply_markup=get_subjects_keyboard()
        )
    else:
        await message.answer("Пожалуйста, выбирай только из предложенных кнопок.", reply_markup=get_subjects_keyboard())

# Дальше оставляем свободный текст, как и было
@router.message(FacultySelection.waiting_for_exams)
async def process_exams(message: Message, state: FSMContext):
    await state.update_data(exams=message.text)
    await state.set_state(FacultySelection.waiting_for_interests)
    text = (
        "Хорошо! 📚\n\n"
        "Расскажи, что тебе интересно? Например: программирование, создание сайтов, работа с техникой, дизайн...\n\n"
        "Опиши своими словами:"
    )
    await message.answer(text)

@router.message(FacultySelection.waiting_for_interests)
async def process_interests(message: Message, state: FSMContext):
    await state.update_data(interests=message.text)
    await state.set_state(FacultySelection.waiting_for_dislikes)
    text = (
        "Замечательно! ✨\n\n"
        "Что тебе точно неинтересно? Это поможет исключить неподходящие направления.\n\n"
        "Опиши своими словами:"
    )
    await message.answer(text)

@router.message(FacultySelection.waiting_for_dislikes)
async def process_dislikes_and_contacts(message: Message, state: FSMContext):
    await state.update_data(dislikes=message.text)
    user = await get_user_by_telegram_id(message.from_user.id)

    need_first_name = not (user and user.first_name)
    need_last_name = not (user and user.last_name)
    need_email = not (user and user.email)
    need_phone = not (user and user.phone)

    user_data = await state.get_data()
    # ВНИМАНИЕ: favorite_subjects и disliked_subjects теперь списки!
    new_user_data = dict(user_data)
    new_user_data["favorite_subjects"] = ", ".join(user_data.get("favorite_subjects", []))
    new_user_data["disliked_subjects"] = ", ".join(user_data.get("disliked_subjects", []))

    recommended_faculty = await get_faculty_recommendation(new_user_data)
    await state.update_data(recommended_faculty=recommended_faculty)

    if need_first_name:
        await state.set_state(FacultySelection.waiting_for_first_name)
        await message.answer("Пожалуйста, введите ваше <b>имя</b>:", parse_mode="HTML")
    elif need_last_name:
        await state.set_state(FacultySelection.waiting_for_last_name)
        await message.answer("Теперь введите вашу <b>фамилию</b>:", parse_mode="HTML")
    elif need_email:
        await state.set_state(FacultySelection.waiting_for_email)
        await message.answer("Введите ваш <b>e-mail</b> для связи:", parse_mode="HTML")
    elif need_phone:
        await state.set_state(FacultySelection.waiting_for_phone)
        await message.answer("Введите ваш контактный <b>телефон</b>:", parse_mode="HTML")
    else:
        await show_faculty_recommendation(message, state)

@router.message(FacultySelection.waiting_for_first_name)
async def process_first_name(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text.strip())
    await state.set_state(FacultySelection.waiting_for_last_name)
    await message.answer("Теперь введите вашу <b>фамилию</b>:", parse_mode="HTML")

@router.message(FacultySelection.waiting_for_last_name)
async def process_last_name(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text.strip())
    await state.set_state(FacultySelection.waiting_for_email)
    await message.answer("Введите ваш <b>e-mail</b> для связи:", parse_mode="HTML")

@router.message(FacultySelection.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text.strip())
    await state.set_state(FacultySelection.waiting_for_phone)
    await message.answer("Введите ваш контактный <b>телефон</b>:", parse_mode="HTML")

@router.message(FacultySelection.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    # Сохраняем новые данные пользователя в БД
    user = await get_user_by_telegram_id(message.from_user.id)
    data = await state.get_data()
    async with async_session() as session:
        if user:
            user.first_name = data.get("first_name") or user.first_name
            user.last_name = data.get("last_name") or user.last_name
            user.email = data.get("email")
            user.phone = data.get("phone")
            session.add(user)
        else:
            user = await create_or_update_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=data.get("first_name"),
                last_name=data.get("last_name")
            )
            user.email = data.get("email")
            user.phone = data.get("phone")
            session.add(user)
        await session.commit()
    await show_faculty_recommendation(message, state)

async def show_faculty_recommendation(message: Message, state: FSMContext):
    data = await state.get_data()
    recommended_faculty = data.get("recommended_faculty")
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
    await state.clear()

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