# Простой тест установки
try:
    import tensorflow as tf
    import numpy as np
    import pymorphy3
    from bot.ml.tusur_model import faculty_predictor
    
    print("✅ Все зависимости установлены успешно!")
    print(f"TensorFlow: {tf.__version__}")
    print(f"NumPy: {np.__version__}")
    print("✅ ML-модель готова к использованию")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
