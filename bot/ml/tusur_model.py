import numpy as np
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
import pymorphy3 as pymorphy2
import os
import pickle
import json
from pathlib import Path

morph = pymorphy2.MorphAnalyzer()

TUSUR_FACULTIES = {
    "РТФ": {
        "name": "Радиотехнический факультет",
        "liked_subjects": ["физика", "математика", "информатика", "алгебра", "геометрия"],
        "disliked_subjects": ["литература", "биология", "история", "обществознание", "мхк"],
        "keywords": ["радиотехника", "электроника", "сигналы", "антенны", "телекоммуникации", "схемотехника", "радио", "связь", "частоты", "волны"]
    },
    "ФЭТ": {
        "name": "Факультет электронной техники", 
        "liked_subjects": ["физика", "математика", "информатика", "технология", "алгебра"],
        "disliked_subjects": ["литература", "история", "обществознание", "мхк", "музыка"],
        "keywords": ["электроника", "микросхемы", "автоматика", "робототехника", "микроконтроллеры", "программирование", "схемы", "процессоры", "датчики", "устройства"]
    },
    "ФСУ": {
        "name": "Факультет систем управления",
        "liked_subjects": ["математика", "информатика", "физика", "обществознание", "экономика"],
        "disliked_subjects": ["биология", "химия", "литература", "мхк", "изо"],
        "keywords": ["управление", "системы", "автоматизация", "менеджмент", "бизнес", "процессы", "оптимизация", "аналитика", "планирование", "контроль"]
    },
    "ГФ": {
        "name": "Гуманитарный факультет",
        "liked_subjects": ["литература", "история", "обществознание", "русский_язык", "английский", "мхк"],
        "disliked_subjects": ["физика", "математика", "химия", "информатика", "алгебра"],
        "keywords": ["психология", "социология", "лингвистика", "культура", "общество", "коммуникации", "языки", "философия", "искусство", "гуманитарные"]
    },
    "ФИТ": {
        "name": "Факультет инновационных технологий",
        "liked_subjects": ["информатика", "математика", "физика", "алгебра", "геометрия"],
        "disliked_subjects": ["биология", "химия", "литература", "история", "мхк"],
        "keywords": ["программирование", "искусственный интеллект", "алгоритмы", "разработка", "it", "инновации", "технологии", "софт", "данные", "цифровые"]
    }
}

SCHOOL_SUBJECTS_LIST = [
    "математика", "русский_язык", "литература", "физика", "химия", 
    "биология", "география", "история", "обществознание", "английский",
    "немецкий", "французский", "китайский", "испанский", "информатика", 
    "технология", "алгебра", "геометрия", "астрономия", "экология", 
    "право", "экономика", "мхк", "изо", "музыка", "черчение", 
    "физкультура", "обж"
]

class TusurFacultyPredictor:
    def __init__(self):
        self.mlb = MultiLabelBinarizer(classes=SCHOOL_SUBJECTS_LIST)
        self.label_encoder = LabelEncoder()
        self.model = None
        self.all_keywords = []
        self.is_trained = False
        self.model_path = Path("bot/ml/trained_model")
        self.model_path.mkdir(parents=True, exist_ok=True)
        
    def lemmatize_text(self, text):
        if not text:
            return ""
        
        words = text.lower().split()
        lemmatized_words = []
        
        for word in words:
            clean_word = ''.join(char for char in word if char.isalpha())
            if clean_word:
                try:
                    parsed = morph.parse(clean_word)[0]
                    lemmatized_words.append(parsed.normal_form)
                except:
                    lemmatized_words.append(clean_word)
        
        return ' '.join(lemmatized_words)
    
    def generate_training_data(self, num_samples=2000):
        data = []
        faculty_codes = list(TUSUR_FACULTIES.keys())

        self.all_keywords = []
        for faculty_info in TUSUR_FACULTIES.values():
            self.all_keywords.extend(faculty_info["keywords"])
        self.all_keywords = list(set(self.all_keywords))
        
        print(f"Генерация {num_samples} образцов для {len(faculty_codes)} факультетов...")
        
        for i in range(num_samples):
            if i % 400 == 0:
                print(f"Сгенерировано {i}/{num_samples} образцов")
                
            faculty_code = np.random.choice(faculty_codes)
            faculty = TUSUR_FACULTIES[faculty_code]

            liked_available = faculty["liked_subjects"].copy()
            liked_count = np.random.randint(2, min(6, len(liked_available) + 1))
            liked = np.random.choice(liked_available, size=min(liked_count, len(liked_available)), replace=False).tolist()

            if np.random.random() < 0.3:
                other_subjects = [s for s in SCHOOL_SUBJECTS_LIST if s not in liked and s not in faculty["disliked_subjects"]]
                if other_subjects:
                    liked.append(np.random.choice(other_subjects))

            disliked_available = faculty["disliked_subjects"].copy()
            disliked_count = np.random.randint(1, min(5, len(disliked_available) + 1))
            disliked = np.random.choice(disliked_available, size=min(disliked_count, len(disliked_available)), replace=False).tolist()

            exams = liked.copy()
            if np.random.random() < 0.4:
                additional_exams = ["русский_язык", "математика", "физика", "информатика", "обществознание"]
                additional = [e for e in additional_exams if e not in exams]
                if additional:
                    exams.append(np.random.choice(additional))

            interests_count = np.random.randint(2, min(4, len(faculty["keywords"])))
            interests_keywords = np.random.choice(faculty["keywords"], size=interests_count, replace=False)
            interests = ", ".join(interests_keywords)

            interest_variations = {
                "программирование": ["программирование", "кодинг", "разработка программ", "написание кода"],
                "электроника": ["электроника", "электронные устройства", "микроэлектроника"],
                "управление": ["управление", "менеджмент", "руководство", "администрирование"],
                "психология": ["психология", "изучение поведения", "работа с людьми"],
                "радиотехника": ["радиотехника", "радиосвязь", "беспроводные технологии"]
            }
            
            for keyword in interests_keywords:
                if keyword in interest_variations and np.random.random() < 0.3:
                    interests = interests.replace(keyword, np.random.choice(interest_variations[keyword]))

            other_faculties = [f for f in faculty_codes if f != faculty_code]
            other_faculty = np.random.choice(other_faculties)
            not_interests_keywords = np.random.choice(TUSUR_FACULTIES[other_faculty]["keywords"], 
                                                     size=min(2, len(TUSUR_FACULTIES[other_faculty]["keywords"])), 
                                                     replace=False)
            not_interests = ", ".join(not_interests_keywords)
            
            data.append({
                "liked_subjects": liked,
                "disliked_subjects": disliked,
                "exams": exams,
                "interests": self.lemmatize_text(interests),
                "not_interests": self.lemmatize_text(not_interests),
                "faculty": faculty_code
            })
        
        print(f"Генерация завершена: {len(data)} образцов")
        return pd.DataFrame(data)
    
    def encode_text_features(self, text, keywords):
        if not text:
            return [0] * len(keywords)
        
        lemmatized = self.lemmatize_text(text)
        encoded = []
        
        for keyword in keywords:
            score = 0
            if keyword in lemmatized:
                score = 1
            elif any(word in lemmatized for word in keyword.split()):
                score = 0.5
            encoded.append(score)
        
        return encoded
    
    def prepare_features(self, df):
        print("Подготовка признаков...")

        liked_encoded = self.mlb.fit_transform(df['liked_subjects'])
        disliked_encoded = self.mlb.transform(df['disliked_subjects'])
        exams_encoded = self.mlb.transform(df['exams'])
        
        print(f"Размеры кодированных предметов: {liked_encoded.shape}")

        interests_encoded = np.array([
            self.encode_text_features(text, self.all_keywords) 
            for text in df['interests']
        ])
        not_interests_encoded = np.array([
            self.encode_text_features(text, self.all_keywords) 
            for text in df['not_interests']
        ])
        
        print(f"Размеры текстовых признаков: {interests_encoded.shape}")

        X = np.hstack([
            liked_encoded,      # 28 признаков
            disliked_encoded,   # 28 признаков  
            exams_encoded,      # 28 признаков
            interests_encoded,  # количество ключевых слов
            not_interests_encoded  # количество ключевых слов
        ])
        
        print(f"Итоговая размерность признаков: {X.shape}")
        return X
    
    def train_model(self, num_samples=2000):
        print("🧠 Начинаем обучение ML модели для ТУСУР...")

        df = self.generate_training_data(num_samples)

        X = self.prepare_features(df)

        y = self.label_encoder.fit_transform(df['faculty'])
        print(f"Факультеты: {list(self.label_encoder.classes_)}")

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        print(f"Обучающая выборка: {X_train.shape}, Тестовая выборка: {X_test.shape}")

        print("Создание нейронной сети...")
        self.model = Sequential([
            Dense(128, activation='relu', input_shape=(X.shape[1],)),
            Dropout(0.3),
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dropout(0.1),
            Dense(len(TUSUR_FACULTIES), activation='softmax')
        ])

        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        print("Архитектура модели:")
        self.model.summary()

        print("Запуск обучения...")
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=100,
            batch_size=32,
            verbose=1
        )

        test_loss, test_accuracy = self.model.evaluate(X_test, y_test, verbose=0)
        print(f"\n✅ Обучение завершено!")
        print(f"Точность на тестовой выборке: {test_accuracy:.3f}")
        
        self.is_trained = True
        return history
    
    def predict_faculty(self, user_data):
        if not self.is_trained:
            print("⚠️ Модель не обучена! Запускаем обучение...")
            self.train_model()
        
        try:
            liked_enc = self.mlb.transform([user_data.get('liked_subjects', [])])
            disliked_enc = self.mlb.transform([user_data.get('disliked_subjects', [])])
            exams_enc = self.mlb.transform([user_data.get('exams', [])])
            
            interests_enc = np.array([
                self.encode_text_features(user_data.get('interests', ''), self.all_keywords)
            ])
            not_interests_enc = np.array([
                self.encode_text_features(user_data.get('not_interests', ''), self.all_keywords)
            ])

            X_input = np.hstack([
                liked_enc,
                disliked_enc,
                exams_enc,
                interests_enc,
                not_interests_enc
            ])

            probabilities = self.model.predict(X_input, verbose=0)[0]
            faculty_index = np.argmax(probabilities)
            faculty_code = self.label_encoder.inverse_transform([faculty_index])[0]
            confidence = probabilities[faculty_index]
            
            faculty_info = TUSUR_FACULTIES[faculty_code]

            explanation = self._generate_explanation(user_data, faculty_code, confidence)
            
            return {
                'code': faculty_code,
                'name': faculty_info['name'],
                'reason': explanation,
                'directions': "• " + "\n• ".join(faculty_info['keywords'][:4]),
                'confidence': float(confidence)
            }
            
        except Exception as e:
            print(f"Ошибка предсказания: {e}")
            return {
                'code': 'ФИТ',
                'name': TUSUR_FACULTIES['ФИТ']['name'],
                'reason': 'Универсальный выбор для современных технологий (fallback)',
                'directions': '• Программирование\n• Инновации\n• IT-технологии',
                'confidence': 0.5
            }
    
    def _generate_explanation(self, user_data, faculty_code, confidence):
        faculty = TUSUR_FACULTIES[faculty_code]
        liked_subjects = user_data.get('liked_subjects', [])
        interests = user_data.get('interests', '')
        
        explanations = []

        matching_subjects = [s for s in liked_subjects if s in faculty['liked_subjects']]
        if matching_subjects:
            explanations.append(f"Ваши любимые предметы ({', '.join(matching_subjects)}) соответствуют профилю факультета")

        matching_keywords = [k for k in faculty['keywords'] if k.lower() in interests.lower()]
        if matching_keywords:
            explanations.append(f"Ваши интересы совпадают с направлениями факультета")

        if confidence > 0.8:
            explanations.append(f"Высокая уверенность модели ({confidence:.1%})")
        elif confidence > 0.6:
            explanations.append(f"Хорошее соответствие ({confidence:.1%})")
        else:
            explanations.append(f"Возможный вариант для рассмотрения ({confidence:.1%})")
        
        return ". ".join(explanations) if explanations else f"Рекомендован системой с уверенностью {confidence:.1%}"
    
    def save_model(self):
        if self.model and self.is_trained:
            model_file = self.model_path / "tusur_model.keras"
            data_file = self.model_path / "model_data.pkl"

            self.model.save(model_file)

            with open(data_file, 'wb') as f:
                pickle.dump({
                    'mlb': self.mlb,
                    'label_encoder': self.label_encoder, 
                    'all_keywords': self.all_keywords,
                    'is_trained': self.is_trained
                }, f)
            
            print(f"✅ Модель сохранена в {model_file}")
            return True
        return False
    
    def load_model(self):
        model_file = self.model_path / "tusur_model.keras"
        data_file = self.model_path / "model_data.pkl"
        
        try:
            if model_file.exists() and data_file.exists():
                from tensorflow.keras.models import load_model

                self.model = load_model(model_file)

                with open(data_file, 'rb') as f:
                    data = pickle.load(f)
                    self.mlb = data['mlb']
                    self.label_encoder = data['label_encoder']
                    self.all_keywords = data['all_keywords']
                    self.is_trained = data.get('is_trained', True)
                
                print(f"✅ Модель загружена из {model_file}")
                return True
            else:
                print("⚠️ Сохраненная модель не найдена, будет создана новая")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            return False

faculty_predictor = TusurFacultyPredictor()

def initialize_model():
    if not faculty_predictor.load_model():
        print("🔄 Первый запуск - обучаем модель...")
        faculty_predictor.train_model()
        faculty_predictor.save_model()

def test_model():
    test_cases = [
        {
            'name': 'IT-ориентированный абитуриент',
            'data': {
                'liked_subjects': ['информатика', 'математика', 'физика'],
                'disliked_subjects': ['литература', 'история'],
                'exams': ['информатика', 'математика'],
                'interests': 'программирование, алгоритмы, разработка',
                'not_interests': 'литература, поэзия'
            }
        },
        {
            'name': 'Технический профиль',
            'data': {
                'liked_subjects': ['физика', 'математика', 'технология'],
                'disliked_subjects': ['обществознание', 'мхк'],
                'exams': ['физика', 'математика'],
                'interests': 'электроника, схемы, автоматика',
                'not_interests': 'гуманитарные науки'
            }
        },
        {
            'name': 'Гуманитарный профиль',
            'data': {
                'liked_subjects': ['литература', 'история', 'обществознание'],
                'disliked_subjects': ['физика', 'математика'],
                'exams': ['литература', 'обществознание'],
                'interests': 'психология, общение, культура',
                'not_interests': 'программирование, техника'
            }
        }
    ]
    
    print("\n🧪 Тестирование модели:")
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        result = faculty_predictor.predict_faculty(test_case['data'])
        print(f"Рекомендация: {result['name']}")
        print(f"Обоснование: {result['reason']}")
        print(f"Уверенность: {result['confidence']:.2%}")

if __name__ == "__main__":
    initialize_model()
    test_model()