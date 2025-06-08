from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import Config
from bot.keyboards.main_menu import get_faculty_choose_keyboard, get_main_menu
from bot.keyboards.subjects_keyboard import get_subjects_keyboard, get_confirm_subjects_keyboard
from bot.data.subjects import SCHOOL_SUBJECTS, EXAM_SUBJECTS
from bot.utils.ml_model import get_faculty_recommendation
from bot.utils.database import get_user_by_telegram_id, add_application, create_or_update_user
import re


def is_valid_phone(phone: str) -> bool:
    digits = re.sub(r'\D', '', phone)
    return len(digits) == 11

def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.fullmatch(pattern, email) is not None


router = Router()


class FacultySelection(StatesGroup):
    selecting_favorite_subjects = State()
    selecting_disliked_subjects = State()
    selecting_exams = State()
    entering_interests = State()
    entering_dislikes = State()
    choosing_faculty = State()
    entering_phone = State()
    entering_email = State()
    confirming_contacts = State()


@router.message(F.text == "🎓 Подобрать факультет")
async def start_faculty_selection(message: Message, state: FSMContext):
    await state.set_state(FacultySelection.selecting_favorite_subjects)
    await state.update_data(selected_favorite_subjects=[])

    text = (
        "Давай подберем тебе подходящий факультет ТУСУР! 🎯\n\n"
        "<b>1/5: Любимые предметы в школе</b>\n\n"
        "Выбери предметы, которые тебе <b>нравятся больше всего</b>.\n"
        "Можно несколько.\n\n"
        "⚠️ <b>Минимум 1 предмет должен быть выбран</b>"
    )
    keyboard = get_subjects_keyboard('school', [])
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("subject_"))
async def toggle_subject_selection(callback: CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    if len(data_parts) < 3:
        await callback.answer("Ошибка формата данных", show_alert=True)
        return

    subject_type = data_parts[1]
    subject_code = "_".join(data_parts[2:])
    current_state = await state.get_state()
    state_data = await state.get_data()

    selected_key = None
    if subject_type == 'school':
        if current_state == FacultySelection.selecting_favorite_subjects.state:
            selected_key = 'selected_favorite_subjects'
        elif current_state == FacultySelection.selecting_disliked_subjects.state:
            selected_key = 'selected_disliked_subjects'
    elif subject_type == 'exam':
        if current_state == FacultySelection.selecting_exams.state:
            selected_key = 'selected_exams'

    if not selected_key:
        await callback.answer("Этот выбор неактуален сейчас.", show_alert=True)
        return

    selected_subjects = state_data.get(selected_key, []).copy()
    if subject_code in selected_subjects:
        selected_subjects.remove(subject_code)
    else:
        selected_subjects.append(subject_code)

    await state.update_data({selected_key: selected_subjects})

    keyboard = get_subjects_keyboard(subject_type, selected_subjects)

    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except:
        await callback.message.delete()
        await callback.message.answer(callback.message.text, reply_markup=keyboard, parse_mode="HTML")

    await callback.answer()


@router.callback_query(F.data == "subjects_school_done")
async def favorite_subjects_done(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_state = await state.get_state()

    if current_state == FacultySelection.selecting_favorite_subjects.state:
        selected_subjects = state_data.get('selected_favorite_subjects', [])
        if not selected_subjects:
            await callback.answer("Выберите хотя бы один предмет!", show_alert=True)
            return
        subjects_text = [f"• {SCHOOL_SUBJECTS.get(code, code)}" for code in selected_subjects]
        confirmation_text = (
                "✅ <b>Любимые предметы выбраны:</b>\n\n" +
                "\n".join(subjects_text) +
                f"\n\n<b>Всего выбрано:</b> {len(selected_subjects)} предм."
        )
        keyboard = get_confirm_subjects_keyboard('favorite')
        await callback.message.edit_text(confirmation_text, reply_markup=keyboard, parse_mode="HTML")

    elif current_state == FacultySelection.selecting_disliked_subjects.state:
        selected_subjects = state_data.get('selected_disliked_subjects', [])
        if not selected_subjects:
            await callback.answer("Выберите хотя бы один предмет!", show_alert=True)
            return
        subjects_text = [f"• {SCHOOL_SUBJECTS.get(code, code)}" for code in selected_subjects]
        confirmation_text = (
                "✅ <b>Нелюбимые предметы выбраны:</b>\n\n" +
                "\n".join(subjects_text) +
                f"\n\n<b>Всего выбрано:</b> {len(selected_subjects)} предм."
        )
        keyboard = get_confirm_subjects_keyboard('disliked')
        await callback.message.edit_text(confirmation_text, reply_markup=keyboard, parse_mode="HTML")

    await callback.answer()


@router.callback_query(F.data == "subjects_exam_done")
async def exams_subjects_done(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    selected_subjects = state_data.get('selected_exams', [])
    if not selected_subjects:
        await callback.answer("Выберите хотя бы один экзамен!", show_alert=True)
        return
    subjects_text = [f"• {EXAM_SUBJECTS.get(code, code)}" for code in selected_subjects]
    confirmation_text = (
            "✅ <b>Планируемые экзамены выбраны:</b>\n\n" +
            "\n".join(subjects_text) +
            f"\n\n<b>Всего выбрано:</b> {len(selected_subjects)} экзам."
    )
    keyboard = get_confirm_subjects_keyboard('exams')
    await callback.message.edit_text(confirmation_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "confirm_favorite_subjects")
async def confirm_favorite_subjects(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FacultySelection.selecting_disliked_subjects)
    await state.update_data(selected_disliked_subjects=[])
    text = (
        "Отлично! 👍\n\n"
        "<b>2/5: Нелюбимые предметы в школе</b>\n\n"
        "Теперь выбери предметы, которые тебе <b>не очень нравятся</b>.\n"
        "Это поможет исключить неподходящие направления.\n\n"
        "⚠️ <b>Минимум 1 предмет должен быть выбран</b>"
    )
    keyboard = get_subjects_keyboard('school', [])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "confirm_disliked_subjects")
async def confirm_disliked_subjects(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FacultySelection.selecting_exams)
    await state.update_data(selected_exams=[])
    text = (
        "Понятно! 📝\n\n"
        "<b>3/5: Планируемые экзамены</b>\n\n"
        "<b>Выбери ЕГЭ для поступления</b> в вуз или ОГЭ для колледжа.\n"
        "Какие экзамены ты планируешь сдавать или уже сдал?\n\n"
        "⚠️ <b>Минимум 1 экзамен должен быть выбран</b>"
    )
    keyboard = get_subjects_keyboard('exam', [])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "confirm_exams_subjects")
async def confirm_exams_subjects(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FacultySelection.entering_interests)
    text = (
        "Хорошо! 📚\n\n"
        "<b>4/5: Что тебе интересно?</b>\n\n"
        "Расскажи подробнее, <b>что тебе интересно</b>?\n"
        "Например: программирование, создание сайтов, работа с техникой, дизайн, научные исследования...\n\n"
        "Опиши подробно своими словами:"
    )
    await callback.message.edit_text(text, reply_markup=None, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("edit_"))
async def edit_subjects_selection(callback: CallbackQuery, state: FSMContext):
    edit_type = callback.data.split("_")[1]
    state_data = await state.get_data()

    if edit_type == 'favorite':
        await state.set_state(FacultySelection.selecting_favorite_subjects)
        selected = state_data.get('selected_favorite_subjects', [])
        subject_type = 'school'
        text = (
            "<b>1/5: Любимые предметы в школе</b>\n\n"
            "Измени выбор предметов, которые тебе <b>нравятся больше всего</b>.\n\n"
            "⚠️ <b>Минимум 1 предмет должен быть выбран</b>"
        )
    elif edit_type == 'disliked':
        await state.set_state(FacultySelection.selecting_disliked_subjects)
        selected = state_data.get('selected_disliked_subjects', [])
        subject_type = 'school'
        text = (
            "<b>2/5: Нелюбимые предметы в школе</b>\n\n"
            "Измени выбор предметов, которые тебе <b>не очень нравятся</b>.\n\n"
            "⚠️ <b>Минимум 1 предмет должен быть выбран</b>"
        )
    else:  # exams
        await state.set_state(FacultySelection.selecting_exams)
        selected = state_data.get('selected_exams', [])
        subject_type = 'exam'
        text = (
            "<b>3/5: Планируемые экзамены</b>\n\n"
            "<b>Выбери ЕГЭ для поступления</b> или ОГЭ для колледжа.\n\n"
            "⚠️ <b>Минимум 1 экзамен должен быть выбран</b>"
        )

    keyboard = get_subjects_keyboard(subject_type, selected)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.message(FacultySelection.entering_interests)
async def process_interests(message: Message, state: FSMContext):
    await state.update_data(interests=message.text)
    await state.set_state(FacultySelection.entering_dislikes)
    text = (
        "Замечательно! ✨\n\n"
        "<b>5/5: Что тебе точно неинтересно?</b>\n\n"
        "<b>Что тебе точно неинтересно</b>? Это поможет исключить неподходящие направления.\n\n"
        "Опиши подробно своими словами:"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(FacultySelection.entering_dislikes)
async def process_dislikes_and_recommend(message: Message, state: FSMContext):
    await state.update_data(dislikes=message.text)
    user_data = await state.get_data()
    ml_data = {
        'favorite_subjects': ", ".join([
            SCHOOL_SUBJECTS.get(code, code) for code in user_data.get('selected_favorite_subjects', [])
        ]),
        'disliked_subjects': ", ".join([
            SCHOOL_SUBJECTS.get(code, code) for code in user_data.get('selected_disliked_subjects', [])
        ]),
        'exams': ", ".join([
            EXAM_SUBJECTS.get(code, code) for code in user_data.get('selected_exams', [])
        ]),
        'interests': user_data.get('interests', ''),
        'dislikes': user_data.get('dislikes', ''),
        'selected_favorite_subjects': user_data.get('selected_favorite_subjects', []),
        'selected_disliked_subjects': user_data.get('selected_disliked_subjects', []),
        'selected_exams': user_data.get('selected_exams', [])
    }
    recommended_faculty = await get_faculty_recommendation(ml_data)
    await state.update_data(
        recommended_faculty_code=recommended_faculty.get('code'),
        recommended_faculty_text=recommended_faculty.get('name'),
        recommendation_reason=recommended_faculty.get('reason')
    )
    await state.set_state(FacultySelection.choosing_faculty)

    faculties_keyboard = get_faculty_choose_keyboard(
        recommended_faculty.get('code'), Config.FACULTIES
    )

    msg = (
        "🧑‍💻 <b>Рекомендованный факультет:</b>\n"
        f"<b>{recommended_faculty['code']} — {recommended_faculty['name']}</b>\n"
        f"<i>{recommended_faculty['reason']}</i>\n\n"
        "Вы также можете выбрать другой факультет, если пожелаете:"
    )

    await message.answer(msg, reply_markup=faculties_keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("faculty_"))
async def choose_faculty_handler(callback: CallbackQuery, state: FSMContext):
    faculty_code = callback.data.replace("faculty_", "", 1)
    faculty_name = Config.FACULTIES.get(faculty_code, faculty_code)
    await state.update_data(selected_faculty_code=faculty_code)

    user = await get_user_by_telegram_id(callback.from_user.id)
    if user and user.phone and user.email:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Все актуально", callback_data="contacts_confirmed"),
                    InlineKeyboardButton(text="✏️ Изменить контактные данные", callback_data="change_contacts")
                ]
            ]
        )
        text = (
            f"<b>Факультет для заявки:</b> {faculty_name}\n\n"
            f"<b>Ваши контакты:</b>\n"
            f"Телефон: {user.phone}\n"
            f"E-mail: {user.email}\n\n"
            "Если все верно — жмите <b>Все актуально</b>\n"
            "Если хотите изменить — нажмите <b>Изменить контактные данные</b>"
        )
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await state.update_data(phone=user.phone, email=user.email)
        await callback.answer()
        return

    await state.set_state(FacultySelection.entering_phone)
    await callback.message.edit_text(
        f"<b>Выбран факультет:</b> {faculty_name}\n\n"
        "Для оформления заявки введите ваш номер телефона (например, +79130000000):",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "change_contacts")
async def change_contacts_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FacultySelection.entering_phone)
    await callback.message.edit_text(
        "Введите новый номер телефона (например, +79130000000):",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "contacts_confirmed")
async def contacts_confirmed_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FacultySelection.confirming_contacts)
    data = await state.get_data()
    faculty_code = data.get("selected_faculty_code")
    phone = data.get("phone")
    email = data.get("email")
    faculty_name = Config.FACULTIES.get(faculty_code, faculty_code)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Подтвердить и отправить заявку", callback_data="submit_application")],
        [InlineKeyboardButton(text="✏️ Изменить выбранные предметы", callback_data="change_subjects")],
        [InlineKeyboardButton(text="✏️ Изменить контактные данные", callback_data="change_contacts_in_confirm")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

    text = (
        f"<b>Проверьте ваши данные:</b>\n\n"
        f"Факультет: <b>{faculty_name}</b>\n"
        f"Телефон: <b>{phone}</b>\n"
        f"E-mail: <b>{email}</b>\n\n"
        "Все верно? Если да — отправьте заявку 👇"
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "change_subjects")
async def change_subjects_from_confirm(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FacultySelection.selecting_favorite_subjects)
    data = await state.get_data()
    selected = data.get('selected_favorite_subjects', [])

    text = (
        "<b>1/5: Любимые предметы в школе</b>\n\n"
        "Измени выбор предметов, которые тебе <b>нравятся больше всего</b>.\n\n"
        "⚠️ <b>Минимум 1 предмет должен быть выбран</b>"
    )
    keyboard = get_subjects_keyboard('school', selected)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "change_contacts_in_confirm")
async def change_contacts_in_confirm(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FacultySelection.entering_phone)
    await callback.message.edit_text(
        "Введите новый номер телефона (например, +79130000000):",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(FacultySelection.entering_phone)
async def ask_email(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not is_valid_phone(phone):
        await message.answer(
            "Некорректный номер телефона!\n"
            "Телефон должен содержать 11 цифр.\n"
            "Пример: <b>+79131234567</b> или <b>89131234567</b>.",
            parse_mode="HTML"
        )
        return
    await state.update_data(phone=phone)
    await state.set_state(FacultySelection.entering_email)
    await message.answer("Пожалуйста, введите ваш E-mail:")


@router.message(FacultySelection.entering_email)
async def finish_contacts_and_confirm(message: Message, state: FSMContext):
    email = message.text.strip()
    if not is_valid_email(email):
        await message.answer(
            "Некорректный E-mail!\n"
            "E-mail должен начинаться с английской буквы, содержать только латинские буквы/цифры, один символ @, "
            "после @ — точка и домен. Пример: <b>ivan123@example.com</b> или <b>test2024@mail.ru</b>",
            parse_mode="HTML"
        )
        return
    await state.update_data(email=email)
    data = await state.get_data()
    faculty_code = data.get("selected_faculty_code")
    faculty_name = Config.FACULTIES.get(faculty_code, faculty_code)
    phone = data.get("phone")

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Подтвердить и отправить заявку", callback_data="submit_application")],
        [InlineKeyboardButton(text="✏️ Изменить выбранные предметы", callback_data="change_subjects")],
        [InlineKeyboardButton(text="✏️ Изменить контактные данные", callback_data="change_contacts_in_confirm")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

    text = (
        f"<b>Проверьте ваши данные:</b>\n\n"
        f"Факультет: <b>{faculty_name}</b>\n"
        f"Телефон: <b>{phone}</b>\n"
        f"E-mail: <b>{email}</b>\n\n"
        "Все верно? Если да — отправьте заявку 👇"
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(FacultySelection.confirming_contacts)


@router.callback_query(F.data == "submit_application")
async def submit_application_callback(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        user = await get_user_by_telegram_id(callback.from_user.id)

        if not user:
            user = await create_or_update_user(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name,
                phone=data.get("phone"),
                email=data.get("email")
            )
        else:
            await create_or_update_user(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name,
                phone=data.get("phone"),
                email=data.get("email")
            )

        faculty_code = data.get("selected_faculty_code")
        if not faculty_code:
            await callback.answer("Ошибка: факультет не выбран.", show_alert=True)
            return

        await add_application(user.id, faculty_code)
        await state.clear()

        faculty_name = Config.FACULTIES.get(faculty_code, faculty_code)
        await callback.message.edit_text(
            f"🎉 Ваша заявка на факультет <b>{faculty_name}</b> успешно подана!\n"
            "В ближайшее время с вами свяжутся сотрудники приемной комиссии.",
            reply_markup=None,
            parse_mode="HTML"
        )

        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_main_menu()
        )
        await callback.answer("Заявка отправлена!", show_alert=True)

    except Exception as e:
        msg = str(e)
        if len(msg) > 150:
            msg = msg[:150] + "..."
        await callback.answer(f"Ошибка при подаче заявки: {msg}", show_alert=True)


@router.callback_query(F.data == "main_menu")
async def return_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Возвращаемся в главное меню.")
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "edit_contacts")
async def edit_contacts_legacy(callback: CallbackQuery, state: FSMContext):
    await change_contacts_handler(callback, state)


@router.callback_query(F.data == "edit_subjects")
async def edit_subjects_legacy(callback: CallbackQuery, state: FSMContext):
    await change_subjects_from_confirm(callback, state)


@router.callback_query(F.data == "edit_subjects_flow")
async def edit_subjects_flow_legacy(callback: CallbackQuery, state: FSMContext):
    await change_subjects_from_confirm(callback, state)


@router.callback_query(F.data == "edit_contacts_flow")
async def edit_contacts_flow_legacy(callback: CallbackQuery, state: FSMContext):
    await change_contacts_in_confirm(callback, state)