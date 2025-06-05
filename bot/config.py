import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///tusur.db")
    DEBUG = os.getenv("DEBUG", "False") == "True"
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

    FACULTIES = {
        "РТФ": "Радиотехнический факультет",
        "ФЭТ": "Факультет электронной техники",
        "ФСУ": "Факультет систем управления",
        "ГФ": "Гуманитарный факультет",
        "ФИТ": "Факультет инновационных технологий"
    }
