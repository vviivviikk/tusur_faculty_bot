from bot.ml.tusur_model import faculty_predictor, initialize_model
from bot.config import Config
import logging
import asyncio

# Флаг инициализации модели
_model_initialized = False

async def ensure_model_initialized():
    """Убеждаемся что модель инициализирована"""
    global _model_initialized
    if not _model_initialized:
        try:
            # Запускаем инициализацию в отдельном потоке
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, initialize_model)
            _model_initialized = True
            logging.info("✅ ML-модель успешно инициализирована")
        except Exception as e:
            logging.error(f"❌ Ошибка инициализации ML-модели: {e}")

async def get_faculty_recommendation(user_data: dict) -> dict:
    """
    Интерфейс для получения рекомендации факультета
    Совместим с существующими handlers
    """
    try:
        # Убеждаемся что модель инициализирована
        await ensure_model_initialized()
        
        # Преобразуем данные в формат новой модели
        processed_data = _prepare_user_data(user_data)
        
        # Получаем рекомендацию от нейросети
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, faculty_predictor.predict_faculty, processed_data)
        
        # Адаптируем результат к ожидаемому формату
        return _format_recommendation(result)
        
    except Exception as e:
        logging.error(f"Ошибка ML-модели: {e}")
        # Fallback к простой логике в случае ошибки
        return _fallback_recommendation(user_data)

def _prepare_user_data(user_data: dict) -> dict:
    """Подготовка данных пользователя для новой модели"""
    
    # Преобразуем строки в списки если нужно
    favorite_subjects = user_data.get('favorite_subjects', '')
    if isinstance(favorite_subjects, str):
        # Парсим строку "математика, физика, информатика"
        favorite_subjects = [s.strip() for s in favorite_subjects.split(',') if s.strip()]
    
    disliked_subjects = user_data.get('disliked_subjects', '')  
    if isinstance(disliked_subjects, str):
        disliked_subjects = [s.strip() for s in disliked_subjects.split(',') if s.strip()]
        
    exams = user_data.get('exams', '')
    if isinstance(exams, str):
        exams = [s.strip() for s in exams.split(',') if s.strip()]
    
    return {
        'liked_subjects': favorite_subjects,
        'disliked_subjects': disliked_subjects, 
        'exams': exams,
        'interests': user_data.get('interests', ''),
        'not_interests': user_data.get('dislikes', '')  # обратите внимание на ключ
    }

def _format_recommendation(ml_result: dict) -> dict:
    """Адаптация результата ML-модели к ожидаемому формату"""
    
    faculty_code = ml_result.get('code', 'ФИТ')
    confidence = ml_result.get('confidence', 0.5)
    
    # Добавляем информацию о confidence в reason
    reason = ml_result.get('reason', 'Рекомендовано системой машинного обучения')
    if confidence > 0.8:
        reason += f" 🎯 (высокая уверенность: {confidence:.0%})"
    elif confidence > 0.6:
        reason += f" ✅ (хорошее соответствие: {confidence:.0%})"
    else:
        reason += f" 🤔 (возможный вариант: {confidence:.0%})"
    
    return {
        'name': Config.FACULTIES.get(faculty_code, ml_result.get('name')),
        'reason': reason,
        'directions': ml_result.get('directions', '• Информационные технологии'),
        'confidence': confidence
    }

def _fallback_recommendation(user_data: dict) -> dict:
    """Резервная рекомендация в случае ошибки ML-модели"""
    
    # Простая логика на основе ключевых слов как fallback
    favorite_subjects = user_data.get('favorite_subjects', '').lower()
    interests = user_data.get('interests', '').lower()
    all_text = f"{favorite_subjects} {interests}"
    
    if any(word in all_text for word in ['информатика', 'программирование', 'it', 'алгоритм']):
        faculty = 'ФИТ'
    elif any(word in all_text for word in ['физика', 'радио', 'связь', 'сигнал']):
        faculty = 'РТФ'
    elif any(word in all_text for word in ['управление', 'менеджмент', 'бизнес', 'система']):
        faculty = 'ФСУ'
    elif any(word in all_text for word in ['электроника', 'автоматика', 'робот', 'техника']):
        faculty = 'ФЭТ'
    elif any(word in all_text for word in ['литература', 'история', 'психология', 'язык']):
        faculty = 'ГФ'
    else:
        faculty = 'ФИТ'  # По умолчанию
    
    return {
        'name': Config.FACULTIES[faculty],
        'reason': 'Базовая рекомендация на основе ключевых слов (резервный алгоритм)',
        'directions': '• Современные технологии\n• Перспективные специальности',
        'confidence': 0.5
    }

# Функция для тестирования ML-модели
async def test_ml_model():
    """Тестирование интеграции ML-модели"""
    test_data = {
        'favorite_subjects': 'информатика, математика, физика',
        'disliked_subjects': 'литература, история',
        'exams': 'информатика, математика',
        'interests': 'программирование, создание сайтов, алгоритмы',
        'dislikes': 'поэзия, искусство'
    }
    
    print("🧪 Тестирование ML-модели...")
    result = await get_faculty_recommendation(test_data)
    print(f"Результат: {result}")
    return result
