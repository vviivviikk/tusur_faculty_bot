from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

SUBJECTS_LIST = [
    "Математика", "Физика", "Информатика",
    "Литература", "История", "Биология",
    "Общество", "Иностранный язык", "География", "Химия"
]

def get_subjects_keyboard():
    rows = []
    for i in range(0, len(SUBJECTS_LIST), 2):
        row = [KeyboardButton(text=SUBJECTS_LIST[i])]
        if i + 1 < len(SUBJECTS_LIST):
            row.append(KeyboardButton(text=SUBJECTS_LIST[i+1]))
        rows.append(row)
    rows.append([KeyboardButton(text="✅ Готово")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=False)