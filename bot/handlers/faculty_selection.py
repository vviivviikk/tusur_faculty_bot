from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import Config
from bot.keyboards.main_menu import get_faculty_inline_keyboard, get_main_menu
from bot.keyboards.subjects import get_subjects_keyboard, get_confirm_subjects_keyboard
from bot.data.subjects import get_subject_name, get_exam_name
from bot.utils.ml_model import get_faculty_recommendation

from bot.utils.database import get_user_by_telegram_id, add_application, create_or_update_user, async_session

router = Router()

class FacultySelection(StatesGroup):
    # Этапы выбора предметов (теперь через inline-кнопки)
    selecting_favorite_subjects = State()
    selecting_disliked_subjects = State()
    selecting_exams = State()
    
    # Этапы текстового ввода (остаются как есть)
    waiting_for_interests = State()
    waiting_for_dislikes = State()
    
    # Этапы заполнения контактов
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_email = State()
    waiting_for_phone = State()

# ========== НАЧАЛО АНКЕТИРОВАНИЯ ==========

@router.message(F.text == "🎓 Подобрать факультет")
async def start_faculty_selection(message: Message, state: FSMContext):
    await state.clear()  # Очищаем предыдущие данные
    await state.set_state(FacultySelection.selecting_favorite_subjects)
    await state.update_data(favorite_subjects=[])
    
    text = (
        "🎯 <b>Подбор факультета ТУСУР</b>\n\n"
        "Ответь на несколько вопросов, и я помогу подобрать факультет, который подходит именно тебе!\n\n"
        "📚 <b>Шаг 1/5:</b> Выбери предметы, которые тебе <b>нравятся</b> в школе:\n\n"
        "💡 <i>Можешь выбрать несколько предметов. Нажимай на кнопки, чтобы добавить/убрать предмет.</i>"
    )
    
    keyboard = get_subjects_keyboard(subject_type="school", selected_subjects=[])
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# ========== ОБРАБОТКА ВЫБОРА ЛЮБИМЫХ ПРЕДМЕТОВ ==========

@router.callback_query(F.data.startswith("subject_school_"), FacultySelection.selecting_favorite_subjects)
async def toggle_favorite_subject(callback: CallbackQuery, state: FSMContext):
    # Извлекаем код предмета из callback_data
    subject_code = callback.data.replace("subject_school_", "")
    
    # Получаем текущий список выбранных предметов
    data = await state.get_data()
    selected_subjects = data.get("favorite_subjects", [])
    
    # Переключаем состояние предмета (toggle)
    if subject_code in selected_subjects:
        selected_subjects.remove(subject_code)
    else:
        selected_subjects.append(subject_code)
    
    # Сохраняем обновленный список
    await state.update_data(favorite_subjects=selected_subjects)
    
    # Обновляем клавиатуру с новым состоянием
    keyboard = get_subjects_keyboard(subject_type="school", selected_subjects=selected_subjects)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer()
    except Exception:
        # Если сообщение не изменилось, просто отвечаем на callback
        await callback.answer()

@router.callback_query(F.data == "subjects_school_done", FacultySelection.selecting_favorite_subjects)
async def confirm_favorite_subjects(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_subjects = data.get("favorite_subjects", [])
    
    if not selected_subjects:
        await callback.answer("⚠️ Выберите хотя бы один предмет!", show_alert=True)
        return
    
    # Показываем выбранные предметы для подтверждения
    selected_names = [get_subject_name(code) for code in selected_subjects]
    text = (
        f"✅ <b>Твои любимые предметы:</b>\n\n"
        f"{'• ' + chr(10) + '• '.join(selected_names)}\n\n"
        f"Всё правильно?"
    )
    
    keyboard = get_confirm_subjects_keyboard("favorite", selected_subjects)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "confirm_favorite_subjects")
async def proceed_to_disliked_subjects(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FacultySelection.selecting_disliked_subjects)
    await state.update_data(disliked_subjects=[])
    
    text = (
        "📚 <b>Шаг 2/5:</b> Выбери предметы, которые тебе <b>НЕ нравятся</b> в школе:\n\n"
        "💡 <i>Это поможет исключить неподходящие направления.</i>"
    )
    
    keyboard = get_subjects_keyboard(subject_type="school", selected_subjects=[])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "edit_favorite_subjects")
async def edit_favorite_subjects(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_subjects = data.get("favorite_subjects", [])
    
    text = (
        "🔄 <b>Редактирование любимых предметов</b>\n\n"
        "📚 Выбери предметы, которые тебе <b>нравятся</b> в школе:"
    )
    
    keyboard = get_subjects_keyboard(subject_type="school", selected_subjects=selected_subjects)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# ========== ОБРАБОТКА ВЫБОРА НЕЛЮБИМЫХ ПРЕДМЕТОВ ==========

@router.callback_query(F.data.startswith("subject_school_"), FacultySelection.selecting_disliked_subjects)
async def toggle_disliked_subject(callback: CallbackQuery, state: FSMContext):
    # Аналогичная логика для нелюбимых предметов
    subject_code = callback.data.replace("subject_school_", "")
    
    data = await state.get_data()
    selected_subjects = data.get("disliked_subjects", [])
    
    # Переключаем состояние предмета
    if subject_code in selected_subjects:
        selected_subjects.remove(subject_code)
    else:
        selected_subjects.append(subject_code)
    
    await state.update_data(disliked_subjects=selected_subjects)
    
    # Обновляем клавиатуру
    keyboard = get_subjects_keyboard(subject_type="school", selected_subjects=selected_subjects)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer()
    except Exception:
        await callback.answer()

@router.callback_query(F.data == "subjects_school_done", FacultySelection.selecting_disliked_subjects)
async def confirm_disliked_subjects(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_subjects = data.get("disliked_subjects", [])
    
    if not selected_subjects:
        await callback.answer("⚠️ Выберите хотя бы один предмет!", show_alert=True)
        return
    
    # Показываем выбранные предметы для подтверждения
    selected_names = [get_subject_name(code) for code in selected_subjects]
    text = (
        f"❌ <b>Предметы, которые тебе НЕ нравятся:</b>\n\n"
        f"{'• ' + chr(10) + '• '.join(selected_names)}\n\n"
        f"Всё правильно?"
    )
    
    keyboard = get_confirm_subjects_keyboard("disliked", selected_subjects)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "confirm_disliked_subjects")
async def proceed_to_exams(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FacultySelection.selecting_exams)
    await state.update_data(exams=[])
    
    text = (
        "📝 <b>Шаг 3/5:</b> Выбери экзамены, которые ты <b>планируешь сдавать</b> или <b>уже сдал</b>:\n\n"
        "💡 <i>Выбери ЕГЭ/ОГЭ которые у тебя есть или будут.</i>"
    )
    
    keyboard = get_subjects_keyboard(subject_type="exam", selected_subjects=[])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "edit_disliked_subjects")
async def edit_disliked_subjects(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_subjects = data.get("disliked_subjects", [])
    
    text = (
        "🔄 <b>Редактирование нелюбимых предметов</b>\n\n"
        "📚 Выбери предметы, которые тебе <b>НЕ нравятся</b>:"
    )
    
    keyboard = get_subjects_keyboard(subject_type="school", selected_subjects=selected_subjects)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# ========== ОБРАБОТКА ВЫБОРА ЭКЗАМЕНОВ ==========

@router.callback_query(F.data.startswith("subject_exam_"), FacultySelection.selecting_exams)
async def toggle_exam(callback: CallbackQuery, state: FSMContext):
    exam_code = callback.data.replace("subject_exam_", "")
    
    data = await state.get_data()
    selected_exams = data.get("exams", [])
    
    # Переключаем состояние экзамена
    if exam_code in selected_exams:
        selected_exams.remove(exam_code)
    else:
        selected_exams.append(exam_code)
    
    await state.update_data(exams=selected_exams)
    
    # Обновляем клавиатуру
    keyboard = get_subjects_keyboard(subject_type="exam", selected_subjects=selected_exams)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer()
    except Exception:
        await callback.answer()

@router.callback_query(F.data == "subjects_exam_done", FacultySelection.selecting_exams)
async def confirm_exams(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_exams = data.get("exams", [])
    
    if not selected_exams:
        await callback.answer("⚠️ Выберите хотя бы один экзамен!", show_alert=True)
        return
    
    # Показываем выбранные экзамены для подтверждения
    selected_names = [get_exam_name(code) for code in selected_exams]
    text = (
        f"📝 <b>Твои экзамены:</b>\n\n"
        f"{'• ' + chr(10) + '• '.join(selected_names)}\n\n"
        f"Всё правильно?"
    )
    
    keyboard = get_confirm_subjects_keyboard("exams", selected_exams)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "confirm_exams_subjects")
async def proceed_to_interests(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FacultySelection.waiting_for_interests)
    
    text = (
        "🌟 <b>Шаг 4/5:</b> Расскажи, что тебе <b>интересно</b>?\n\n"
        "💡 <i>Например: программирование, создание сайтов, работа с техникой, дизайн, роботы, управление, психология...</i>\n\n"
        "✍️ <b>Опиши своими словами:</b>"
    )
    
    await callback.message.edit_text(text, reply_markup=None, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "edit_exams_subjects")
async def edit_exams(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_exams = data.get("exams", [])
    
    text = (
        "🔄 <b>Редактирование экзаменов</b>\n\n"
        "📝 Выбери экзамены, которые ты планируешь сдавать:"
    )
    
    keyboard = get_subjects_keyboard(subject_type="exam", selected_subjects=selected_exams)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# ========== ТЕКСТОВЫЕ ПОЛЯ (ИНТЕРЕСЫ И НЕИНТЕРЕСЫ) ==========

@router.message(FacultySelection.waiting_for_interests)
async def process_interests(message: Message, state: FSMContext):
    await state.update_data(interests=message.text)
    await state.set_state(FacultySelection.waiting_for_dislikes)
    
    text = (
        "🚫 <b>Шаг 5/5:</b> Что тебе точно <b>НЕинтересно</b>?\n\n"
        "💡 <i>Это поможет исключить неподходящие направления. Например: скучная теория, однообразная работа, гуманитарные науки...</i>\n\n"
        "✍️ <b>Опиши своими словами:</b>"
    )
    
    await message.answer(text, parse_mode="HTML")

@router.message(FacultySelection.waiting_for_dislikes)
async def process_dislikes_and_get_recommendation(message: Message, state: FSMContext):
    await state.update_data(dislikes=message.text)
    
    # Отправляем "машинка печатает" для красоты
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    # Получаем данные пользователя
    user = await get_user_by_telegram_id(message.from_user.id)
    
    # Проверяем какие данные нужно собрать
    need_first_name = not (user and user.first_name)
    need_last_name = not (user and user.last_name)
    need_email = not (user and user.email)
    need_phone = not (user and user.phone)
    
    # Подготавливаем данные для ML-модели
    user_data = await state.get_data()
    ml_data = {
        "favorite_subjects": user_data.get("favorite_subjects", []),
        "disliked_subjects": user_data.get("disliked_subjects", []),
        "exams": user_data.get("exams", []),
        "interests": user_data.get("interests", ""),
        "dislikes": user_data.get("dislikes", "")
    }
    
    # Получаем рекомендацию от ML-модели
    recommended_faculty = await get_faculty_recommendation(ml_data)
    await state.update_data(recommended_faculty=recommended_faculty)
    
    # Если нужны дополнительные данные, собираем их
    if need_first_name:
        await state.set_state(FacultySelection.waiting_for_first_name)
        await message.answer(
            "📋 <b>Почти готово!</b> Для подачи заявки нужно несколько данных.\n\n"
            "👤 Введите ваше <b>имя</b>:",
            parse_mode="HTML"
        )
    elif need_last_name:
        await state.set_state(FacultySelection.waiting_for_last_name)
        await message.answer("👤 Введите вашу <b>фамилию</b>:", parse_mode="HTML")
    elif need_email:
        await state.set_state(FacultySelection.waiting_for_email)
        await message.answer("📧 Введите ваш <b>email</b> для связи:", parse_mode="HTML")
    elif need_phone:
        await state.set_state(FacultySelection.waiting_for_phone)
        await message.answer("📱 Введите ваш контактный <b>телефон</b>:", parse_mode="HTML")
    else:
        # Все данные есть, показываем результат
        await show_faculty_recommendation(message, state)

# ========== СБОР КОНТАКТНЫХ ДАННЫХ ==========

@router.message(FacultySelection.waiting_for_first_name)
async def process_first_name(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text.strip())
    await state.set_state(FacultySelection.waiting_for_last_name)
    await message.answer("👤 Введите вашу <b>фамилию</b>:", parse_mode="HTML")

@router.message(FacultySelection.waiting_for_last_name)
async def process_last_name(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text.strip())
    await state.set_state(FacultySelection.waiting_for_email)
    await message.answer("📧 Введите ваш <b>email</b> для связи:", parse_mode="HTML")

@router.message(FacultySelection.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    email = message.text.strip()
    
    # Простая валидация email
    if "@" not in email or "." not in email:
        await message.answer("❌ Неверный формат email. Попробуйте ещё раз:")
        return
    
    await state.update_data(email=email)
    await state.set_state(FacultySelection.waiting_for_phone)
    await message.answer("📱 Введите ваш контактный <b>телефон</b>:", parse_mode="HTML")

@router.message(FacultySelection.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    
    # Сохраняем данные пользователя в БД
    await save_user_data(message, state)
    
    # Показываем рекомендацию
    await show_faculty_recommendation(message, state)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

async def save_user_data(message: Message, state: FSMContext):
    """Сохранение данных пользователя в БД"""
    user = await get_user_by_telegram_id(message.from_user.id)
    data = await state.get_data()
    
    async with async_session() as session:
        if user:
            # Обновляем существующего пользователя
            user.first_name = data.get("first_name") or user.first_name
            user.last_name = data.get("last_name") or user.last_name
            user.email = data.get("email") or user.email
            user.phone = data.get("phone") or user.phone
            session.add(user)
        else:
            # Создаем нового пользователя
            user = await create_or_update_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=data.get("first_name", message.from_user.first_name),
                last_name=data.get("last_name", message.from_user.last_name)
            )
            user.email = data.get("email")
            user.phone = data.get("phone")
            session.add(user)
        
        await session.commit()

async def show_faculty_recommendation(message: Message, state: FSMContext):
    """Показ рекомендации факультета"""
    data = await state.get_data()
    recommended_faculty = data.get("recommended_faculty")
    
    confidence = recommended_faculty.get('confidence', 0.5)
    confidence_emoji = "🎯" if confidence > 0.8 else "✅" if confidence > 0.6 else "🤔"
    
    text = (
        f"🎓 <b>Анализ завершен!</b>\n\n"
        f"{confidence_emoji} <b>Рекомендуемый факультет:</b>\n"
        f"<b>{recommended_faculty['name']}</b>\n\n"
        f"💭 <b>Почему именно он:</b>\n"
        f"{recommended_faculty['reason']}\n\n"
        f"📚 <b>Основные направления:</b>\n"
        f"{recommended_faculty['directions']}\n\n"
        f"Хотите подать заявку на этот факультет?"
    )
    
    keyboard = get_faculty_inline_keyboard(Config.FACULTIES)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.clear()

# ========== ОБРАБОТКА ВОЗВРАТА В ГЛАВНОЕ МЕНЮ ==========

@router.callback_query(F.data == "main_menu")
async def return_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Возвращаемся в главное меню:",
        reply_markup=get_main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    """Игнорируем нажатия на неактивные кнопки"""
    await callback.answer()

# ========== СУЩЕСТВУЮЩИЕ ОБРАБОТЧИКИ ЗАЯВОК ==========

@router.callback_query(F.data == "submit_application")
async def submit_application_callback(callback: CallbackQuery, state: FSMContext):
    try:
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
        await callback.answer(f"Ошибка при подаче заявки: {str(e)}", show_alert=True)

@router.callback_query(F.data.startswith("faculty_"))
async def select_faculty_callback(callback: CallbackQuery, state: FSMContext):
    faculty_code = callback.data.split("_")[1]
    faculty_name = Config.FACULTIES.get(faculty_code, "Неизвестный факультет")
    
    text = (
        f"✅ <b>Выбран факультет:</b> {faculty_name}\n\n"
        "Хотите подать заявку на обучение на этом факультете?"
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Да, подать заявку", callback_data="submit_application")],
        [InlineKeyboardButton(text="🔄 Выбрать другой факультет", callback_data="choose_another")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await state.update_data(selected_faculty_code=faculty_code)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "choose_another")
async def choose_another_faculty(callback: CallbackQuery):
    keyboard = get_faculty_inline_keyboard(Config.FACULTIES)
    text = "Выберите другой факультет:"
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
