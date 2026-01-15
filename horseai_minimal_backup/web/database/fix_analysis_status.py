import django
import os
import sys

sys.path.append('/home/ais/shared/horseAI/horseai_project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horseai_project.settings')
django.setup()

from django.db import connection

# Проверяем есть ли поле в базе данных
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'database_video' 
        AND COLUMN_NAME = 'analysis_status'
    """)
    result = cursor.fetchone()
    
    if result:
        print("✅ Поле analysis_status уже существует в таблице")
    else:
        print("❌ Поле analysis_status не найдено, добавляем...")
        try:
            cursor.execute("ALTER TABLE database_video ADD COLUMN analysis_status VARCHAR(20) DEFAULT 'pending'")
            print("✅ Поле analysis_status успешно добавлено")
        except Exception as e:
            print(f"❌ Ошибка при добавлении поля: {e}")

# Обновляем существующие записи через RAW SQL
with connection.cursor() as cursor:
    cursor.execute("UPDATE database_video SET analysis_status = 'completed' WHERE analysis_status IS NULL")
    print("✅ Существующие записи обновлены")
