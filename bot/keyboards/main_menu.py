from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎓 Подобрать факультет")],
            [KeyboardButton(text="📝 Мои заявки"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )

def get_faculty_inline_keyboard(faculties):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for code, name in faculties.items():
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{code} - {name}",
                callback_data=f"faculty_{code}"
            )
        ])
    # Убираем кнопку "📋 Подать заявку" отсюда!
    return keyboard