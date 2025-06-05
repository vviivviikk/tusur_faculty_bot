from bot.config import Config
import re


async def get_faculty_recommendation(user_data: dict) -> dict:
    """
    Простая логика подбора факультета на основе ключевых слов
    Использует правила if-else вместо машинного обучения
    """

    # Получаем данные пользователя
    favorite_subjects = user_data.get('favorite_subjects', '').lower()
    interests = user_data.get('interests', '').lower()
    exams = user_data.get('exams', '').lower()

    # Объединяем все текстовые данные
    all_text = f"{favorite_subjects} {interests} {exams}"

    # Определяем факультеты по ключевым словам
    faculty_scores = {}

    # Правила для ФИТ (Факультет инновационных технологий)
    fit_keywords = ['программирование', 'информатика', 'компьютер', 'сайт', 'приложение',
                    'код', 'python', 'java', 'javascript', 'it', 'айти', 'разработка']
    fit_score = sum(1 for keyword in fit_keywords if keyword in all_text)
    faculty_scores['ФИТ'] = fit_score

    # Правила для РТФ (Радиотехнический факультет)
    rtf_keywords = ['физика', 'математика', 'радио', 'электроника', 'техника',
                    'схемы', 'электричество', 'сигналы', 'антенна']
    rtf_score = sum(1 for keyword in rtf_keywords if keyword in all_text)
    faculty_scores['РТФ'] = rtf_score

    # Правила для ФЭТ (Факультет электронной техники)
    fet_keywords = ['электроника', 'микросхемы', 'процессор', 'электротехника',
                    'схемотехника', 'автоматика', 'робототехника']
    fet_score = sum(1 for keyword in fet_keywords if keyword in all_text)
    faculty_scores['ФЭТ'] = fet_score

    # Правила для ФСУ (Факультет систем управления)
    fsu_keywords = ['управление', 'системы', 'автоматизация', 'контроль',
                    'менеджмент', 'бизнес', 'процессы', 'организация']
    fsu_score = sum(1 for keyword in fsu_keywords if keyword in all_text)
    faculty_scores['ФСУ'] = fsu_score

    # Правила для ГФ (Гуманитарный факультет)
    gf_keywords = ['литература', 'история', 'язык', 'общение', 'психология',
                   'социология', 'философия', 'культура', 'искусство']
    gf_score = sum(1 for keyword in gf_keywords if keyword in all_text)
    faculty_scores['ГФ'] = gf_score

    # Находим факультет с максимальным количеством совпадений
    best_faculty = max(faculty_scores, key=faculty_scores.get)
    max_score = faculty_scores[best_faculty]

    # Если нет явных совпадений, рекомендуем ФИТ как универсальный
    if max_score == 0:
        best_faculty = 'ФИТ'

    # Формируем ответ в зависимости от выбранного факультета
    recommendations = {
        'ФИТ': {
            'name': Config.FACULTIES['ФИТ'],
            'reason': 'Твои интересы к современным технологиям и программированию идеально подходят для ФИТ',
            'directions': '• Программная инженерия\n• Информационные системы\n• Искусственный интеллект\n• Веб-разработка'
        },
        'РТФ': {
            'name': Config.FACULTIES['РТФ'],
            'reason': 'Твой интерес к физике и технике отлично подходит для радиотехнического направления',
            'directions': '• Радиотехника\n• Электроника и наноэлектроника\n• Телекоммуникации\n• Радиосвязь'
        },
        'ФЭТ': {
            'name': Config.FACULTIES['ФЭТ'],
            'reason': 'Интерес к электронике и автоматике делает ФЭТ отличным выбором для тебя',
            'directions': '• Электронная техника\n• Автоматика и управление\n• Робототехника\n• Микроэлектроника'
        },
        'ФСУ': {
            'name': Config.FACULTIES['ФСУ'],
            'reason': 'Твои склонности к управлению и организации процессов подходят для ФСУ',
            'directions': '• Управление в технических системах\n• Бизнес-информатика\n• Менеджмент\n• Системный анализ'
        },
        'ГФ': {
            'name': Config.FACULTIES['ГФ'],
            'reason': 'Твой интерес к гуманитарным наукам и общению людьми подходит для ГФ',
            'directions': '• Лингвистика\n• Психология\n• Социология\n• Культурология'
        }
    }

    return recommendations[best_faculty]
