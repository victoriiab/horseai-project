import MySQLdb
import os

# Данные подключения к базе данных
db_config = {
    'host': 'localhost',
    'user': 'horseai_user',
    'passwd': 'KVA437',
    'db': 'horseai_db'
}

try:
    # Подключаемся к базе данных
    conn = MySQLdb.connect(**db_config)
    cursor = conn.cursor()
    
    # Проверяем есть ли поле analysis_status
    cursor.execute("DESCRIBE database_video")
    columns = [col[0] for col in cursor.fetchall()]
    
    if 'analysis_status' in columns:
        print("✅ Поле analysis_status уже существует в таблице database_video")
    else:
        # Добавляем поле
        cursor.execute("ALTER TABLE database_video ADD COLUMN analysis_status VARCHAR(20) DEFAULT 'pending'")
        print("✅ Поле analysis_status успешно добавлено в таблицу database_video")
    
    # Обновляем существующие записи
    cursor.execute("UPDATE database_video SET analysis_status = 'completed' WHERE analysis_status IS NULL")
    updated_count = cursor.rowcount
    print(f"✅ Обновлено {updated_count} записей в таблице database_video")
    
    # Сохраняем изменения
    conn.commit()
    cursor.close()
    conn.close()
    
    print("🎉 База данных успешно обновлена!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
