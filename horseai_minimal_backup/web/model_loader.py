# /home/ais/shared/horseAI/web/model_loader.py
import sys
import joblib
import pickle
from pathlib import Path

def load_your_model():
    """Загружает вашу модель с исправленными импортами"""
    
    # Добавляем все нужные пути
    sys.path.insert(0, '/home/ais/shared/horseAI')
    sys.path.insert(0, '/home/ais/shared/horseAI/models')
    sys.path.insert(0, '/home/ais/shared/horseAI/models/modules')
    
    # Создаем кастомный unpickler для исправления импортов
    class ModelUnpickler(pickle.Unpickler):
        def find_class(self, module, name):
            # Исправляем неправильные импорты
            # Модель ожидает: models.random_forest.MyRandomForest
            # Но реальный путь: models.modules.random_forest.MyRandomForest
            
            if module.startswith('models.'):
                # Заменяем models. на models.modules.
                fixed_module = module.replace('models.', 'models.modules.', 1)
                try:
                    # Динамически импортируем модуль
                    __import__(fixed_module)
                    module_obj = sys.modules[fixed_module]
                    return getattr(module_obj, name)
                except (ImportError, AttributeError):
                    # Если не получилось, пробуем оригинальный путь
                    pass
            
            # Для остальных используем стандартный импорт
            return super().find_class(module, name)
    
    # Загружаем модель
    model_path = Path('/home/ais/shared/horseAI/models/trained/model.pkl')
    
    with open(model_path, 'rb') as f:
        unpickler = ModelUnpickler(f)
        model_data = unpickler.load()
    
    return model_data

# Тест загрузки
if __name__ == "__main__":
    try:
        model_data = load_your_model()
        print("✓ Модель загружена!")
        print("Ключи:", list(model_data.keys()))
        
        if 'scaler' in model_data:
            print("✓ Scaler загружен")
            
        if 'hybrid_model' in model_data:
            print("✓ Hybrid model загружена")
            
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
