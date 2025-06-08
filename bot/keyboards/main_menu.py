from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎓 Подобрать факультет")],
            [KeyboardButton(text="📝 Мои заявки"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True,
        persistent=True
    )

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отменить")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )

def get_faculty_choose_keyboard(main_code: str, faculties: dict):
    faculty_list = [code for code in faculties.keys() if code != main_code]
    inline_keyboard = [
        [InlineKeyboardButton(
            text=f"✅ {main_code} — {faculties[main_code]}", callback_data=f"faculty_{main_code}"
        )]
    ]
    for code in faculty_list:
        inline_keyboard.append([InlineKeyboardButton(
            text=f"{code} — {faculties[code]}", callback_data=f"faculty_{code}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def get_faculty_inline_keyboard(faculties):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for code, name in faculties.items():
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{code} - {name[:20]}...",
                callback_data=f"faculty_{code}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="📋 Подать заявку",
            callback_data="submit_application"
        )
    ])


    return keyboard
