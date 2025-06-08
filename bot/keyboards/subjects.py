from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.data.subjects import SCHOOL_SUBJECTS, EXAM_SUBJECTS

def get_subjects_keyboard(subject_type: str = "school", selected_subjects: list = None) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора предметов с checkbox функционалом
    
    Args:
        subject_type: 'school' для школьных предметов, 'exam' для экзаменов
        selected_subjects: список уже выбранных предметов (коды)
    """
    if selected_subjects is None:
        selected_subjects = []
    
    subjects_dict = SCHOOL_SUBJECTS if subject_type == "school" else EXAM_SUBJECTS
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Создаем кнопки по 2 в ряд для удобства
    buttons_row = []
    for subject_code, subject_name in subjects_dict.items():
        # Добавляем ✅ если предмет выбран
        display_text = f"✅ {subject_name}" if subject_code in selected_subjects else subject_name
        
        button = InlineKeyboardButton(
            text=display_text,
            callback_data=f"subject_{subject_type}_{subject_code}"
        )
        
        buttons_row.append(button)
        
        # Добавляем ряд если собрали 2 кнопки
        if len(buttons_row) == 2:
            keyboard.inline_keyboard.append(buttons_row)
            buttons_row = []
    
    # Добавляем оставшуюся кнопку если есть
    if buttons_row:
        keyboard.inline_keyboard.append(buttons_row)
    
    # Разделитель
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="─────────────────", callback_data="ignore")
    ])
    
    # Показываем количество выбранных предметов
    count_text = f"📊 Выбрано: {len(selected_subjects)}"
    if len(selected_subjects) == 0:
        count_text += " (нужен минимум 1)"
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text=count_text, callback_data="ignore")
    ])
    
    # Кнопка "Далее" (активна только если выбран хотя бы 1 предмет)
    if len(selected_subjects) > 0:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="➡️ Продолжить",
                callback_data=f"subjects_{subject_type}_done"
            )
        ])
    else:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="⚠️ Выберите хотя бы 1 предмет",
                callback_data="ignore"
            )
        ])
    
    # Кнопка отмены
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )
    ])
    
    return keyboard

def get_confirm_subjects_keyboard(subject_type: str, selected_subjects: list) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения выбора предметов"""
    from bot.data.subjects import get_subjects_by_codes, get_exams_by_codes
    
    if subject_type == "school":
        selected_names = get_subjects_by_codes(selected_subjects)
    else:
        selected_names = get_exams_by_codes(selected_subjects)
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Подтвердить выбор",
            callback_data=f"confirm_{subject_type}_subjects"
        )],
        [InlineKeyboardButton(
            text="🔄 Изменить выбор", 
            callback_data=f"edit_{subject_type}_subjects"
        )],
        [InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )]
    ])

# Оставляем для совместимости со старым кодом
SUBJECTS_LIST = list(SCHOOL_SUBJECTS.keys())