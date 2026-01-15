#!/usr/bin/env python3
"""
Выносим функцию get_lameness_status изнутри другой функции
"""

with open('upload_lameness.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим строки с функцией get_lameness_status (строки 1195-1215 в оригинале)
# Но в массиве lines индексы с 0
output_lines = []
i = 0
in_nested_function = False
nested_function_lines = []

while i < len(lines):
    line = lines[i]
    
    # Ищем начало вложенной функции
    if 'def get_lameness_status(request, video_id):' in line and not line.startswith('    '):
        print(f"Найдена неправильно расположенная функция на строке {i+1}")
        in_nested_function = True
        
        # Сохраняем эту строку для перемещения
        nested_function_lines.append(line)
        i += 1
        continue
    
    # Если внутри вложенной функции
    if in_nested_function:
        # Добавляем строку в буфер
        nested_function_lines.append(line)
        
        # Проверяем конец функции (пустая строка или начало новой функции)
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            if next_line.strip() == '' or next_line.lstrip().startswith('def '):
                # Нашли конец функции
                in_nested_function = False
                print(f"Найден конец вложенной функции на строке {i+1}")
        i += 1
        continue
    
    # Обычная строка
    output_lines.append(line)
    i += 1

# Теперь вставляем функцию в правильное место (после всех других функций)
# Найдем место после всех функций
insert_index = -1
for j in range(len(output_lines)):
    if output_lines[j].strip().startswith('def ') and j > insert_index:
        insert_index = j

# Вставляем функцию после последней найденной функции
if insert_index != -1 and nested_function_lines:
    # Найдем конец этой функции
    end_index = insert_index
    while end_index < len(output_lines) and (output_lines[end_index].strip() != '' or output_lines[end_index+1:end_index+3].count('\n') < 2):
        end_index += 1
    
    # Вставляем после функции
    insert_pos = end_index + 1
    print(f"Вставляем функцию после строки {insert_pos}")
    
    # Добавляем пустую строку перед функцией
    output_lines.insert(insert_pos, '\n')
    insert_pos += 1
    
    # Вставляем функцию
    for func_line in nested_function_lines:
        output_lines.insert(insert_pos, func_line)
        insert_pos += 1
    
    print(f"✅ Функция перемещена")

# Сохраняем исправленный файл
with open('upload_lameness_fixed.py', 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print("✅ Создан исправленный файл: upload_lameness_fixed.py")
