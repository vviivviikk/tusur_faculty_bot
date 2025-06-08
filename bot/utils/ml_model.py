from bot.ml.tusur_model import faculty_predictor
from bot.data.subjects import SCHOOL_SUBJECTS, EXAM_SUBJECTS

async def get_faculty_recommendation(user_data):

    favorite_subjects_codes = user_data.get('selected_favorite_subjects', [])
    disliked_subjects_codes = user_data.get('selected_disliked_subjects', [])
    exam_codes = user_data.get('selected_exams', [])

    favorite_subjects = []
    for code in favorite_subjects_codes:
        if code in SCHOOL_SUBJECTS:
            favorite_subjects.append(code)
    
    disliked_subjects = []
    for code in disliked_subjects_codes:
        if code in SCHOOL_SUBJECTS:
            disliked_subjects.append(code)

    exams = []
    for code in exam_codes:
        if code in EXAM_SUBJECTS:
            clean_code = code.replace('_ege', '').replace('_oge', '')
            exams.append(clean_code)

    ml_input = {
        'liked_subjects': favorite_subjects,
        'disliked_subjects': disliked_subjects,
        'exams': exams,
        'interests': user_data.get('interests', ''),
        'not_interests': user_data.get('dislikes', '')
    }
    
    try:
        prediction = faculty_predictor.predict_faculty(ml_input)

        return {
            'code': prediction['code'],
            'name': prediction['name'],
            'reason': prediction['reason'],
            'directions': prediction['directions']
        }
        
    except Exception as e:
        print(f"Ошибка ML модели: {e}")
        return await simple_faculty_recommendation(user_data)

async def simple_faculty_recommendation(user_data):

    from bot.config import Config
    
    favorite_subjects_codes = user_data.get('selected_favorite_subjects', [])
    interests = user_data.get('interests', '').lower()

    if 'информатика' in favorite_subjects_codes or any(word in interests for word in ['программирование', 'кодинг', 'разработка', 'алгоритмы']):
        return {
            'code': 'ФИТ',
            'name': Config.FACULTIES['ФИТ'],
            'reason': 'Рекомендован на основе интереса к программированию и информатике',
            'directions': '• Программная инженерия\n• Искусственный интеллект\n• Информационные системы\n• Цифровые технологии'
        }
    elif 'физика' in favorite_subjects_codes or any(word in interests for word in ['радио', 'электроника', 'сигналы', 'связь']):
        return {
            'code': 'РТФ', 
            'name': Config.FACULTIES['РТФ'],
            'reason': 'Подходит для интересующихся физикой и радиотехникой',
            'directions': '• Радиотехника\n• Электроника и наноэлектроника\n• Телекоммуникации\n• Радиосвязь'
        }
    elif any(word in interests for word in ['управление', 'менеджмент', 'бизнес', 'экономика']):
        return {
            'code': 'ФСУ',
            'name': Config.FACULTIES['ФСУ'],
            'reason': 'Соответствует интересам в области управления и бизнеса',
            'directions': '• Управление в технических системах\n• Бизнес-информатика\n• Менеджмент\n• Системный анализ'
        }
    elif any(word in interests for word in ['психология', 'общение', 'языки', 'культура']):
        return {
            'code': 'ГФ',
            'name': Config.FACULTIES['ГФ'],
            'reason': 'Подходит для гуманитарно ориентированных абитуриентов',
            'directions': '• Лингвистика\n• Психология\n• Социология\n• Культурология'
        }
    elif any(subject in favorite_subjects_codes for subject in ['физика', 'технология']) or any(word in interests for word in ['автоматика', 'робототехника', 'устройства']):
        return {
            'code': 'ФЭТ',
            'name': Config.FACULTIES['ФЭТ'],
            'reason': 'Рекомендован для интересующихся электронной техникой',
            'directions': '• Электронная техника\n• Автоматика и управление\n• Робототехника\n• Микроэлектроника'
        }
    else:
        return {
            'code': 'ФИТ',
            'name': Config.FACULTIES['ФИТ'], 
            'reason': 'Универсальный выбор для современных технологий и инноваций',
            'directions': '• Информационные технологии\n• Цифровая экономика\n• Инновационные проекты\n• Современные технологии'
        }

async def initialize_ml_model():
    try:
        if not faculty_predictor.load_model():
            print("🤖 Первый запуск ML модели - начинаем обучение...")
            faculty_predictor.train_model(num_samples=1500)
            faculty_predictor.save_model()
        print("✅ ML модель готова к работе!")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации ML модели: {e}")
        print("Будет использоваться простая логика как fallback")
