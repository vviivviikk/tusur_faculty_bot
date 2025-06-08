from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.data.subjects import SCHOOL_SUBJECTS, EXAM_SUBJECTS

def get_subjects_keyboard(subject_type: str, selected_subjects: list = None) -> InlineKeyboardMarkup:
    if selected_subjects is None:
        selected_subjects = []
    subjects_dict = SCHOOL_SUBJECTS if subject_type == 'school' else EXAM_SUBJECTS
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    subjects = list(subjects_dict.items())
    for i in range(0, len(subjects), 2):
        row = []
        for j in range(2):
            if i + j >= len(subjects):
                break
            code, name = subjects[i + j]
            checked = "✅ " if code in selected_subjects else ""
            row.append(InlineKeyboardButton(
                text=f"{checked}{name}",
                callback_data=f"subject_{subject_type}_{code}"
            ))
        keyboard.inline_keyboard.append(row)
    count = len(selected_subjects)
    control_row = [InlineKeyboardButton(
        text=f"Выбрано: {count}" + (" (мин. 1)" if count == 0 else ""),
        callback_data="ignore"
    )]
    keyboard.inline_keyboard.append(control_row)
    if count > 0:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="➡️ Далее", callback_data=f"subjects_{subject_type}_done")
        ])
    else:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="❌ Выберите хотя бы 1 предмет", callback_data="ignore")
        ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    return keyboard

def get_confirm_subjects_keyboard(subject_type: str) -> InlineKeyboardMarkup:
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