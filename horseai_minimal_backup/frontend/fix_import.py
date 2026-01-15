#!/usr/bin/env python3
import sys
import os

# Добавляем путь к scripts
scripts_path = '/home/ais/shared/horseAI/scripts'
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

# Теперь импортируем
try:
    from api import super_admin_views
    print(f"✅ Успешно импортированы функции:")
    
    # Проверим какие функции есть
    functions = [f for f in dir(super_admin_views) if f.startswith('super_admin_')]
    print(f"Найдено {len(functions)} функций:")
    for func in sorted(functions)[:10]:  # Первые 10
        print(f"  - {func}")
    
    # Проверим несколько конкретных функций
    important_funcs = [
        'super_admin_users',
        'super_admin_stats', 
        'super_admin_system_health',
        'super_admin_videos',
        'super_admin_analyses'
    ]
    
    print(f"\n✅ Проверка ключевых функций:")
    for func in important_funcs:
        if hasattr(super_admin_views, func):
            print(f"  ✓ {func} - найдена")
        else:
            print(f"  ✗ {func} - НЕ найдена")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"Python path: {sys.path}")
