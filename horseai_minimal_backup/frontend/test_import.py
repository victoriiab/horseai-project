import sys
sys.path.insert(0, '/home/ais/shared/horseAI')

try:
    from web.database.models import Animal
    print("✅ Успешный импорт из web.database.models")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    
    # Попробуем другой путь
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("database.models", "/home/ais/shared/horseAI/web/database/models.py")
        database_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(database_module)
        print("✅ Успешный импорт через importlib")
    except Exception as e2:
        print(f"❌ Вторая ошибка: {e2}")
