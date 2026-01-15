#!/usr/bin/env python3
"""
Создаем полностью исправленный файл с правильной структурой
"""

import re

# Читаем старый файл
with open('/home/ais/shared/horseAI/web/upload_lameness.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Разделяем на части: до функции, сама функция, после функции
pattern = r'(\s+def get_lameness_status\(request, video_id\):\s*"""Получение статуса""".*?)(?=\n\S|\Z)'

# Находим функцию
match = re.search(pattern, content, re.DOTALL)
if not match:
    print("❌ Не удалось найти функцию get_lameness_status")
    exit(1)

function_text = match.group(1)
before_function = content[:match.start()]
after_function = content[match.end():]

# Проверяем отступы функции - должны быть на верхнем уровне (не внутри другой функции)
# Убираем все отступы в начале функции
lines = function_text.split('\n')
fixed_lines = []

for i, line in enumerate(lines):
    if i == 0:  # def строка
        fixed_lines.append(line.lstrip())
    else:
        # Сохраняем отступы тела функции (4 пробела)
        if line.strip():  # Не пустая строка
            fixed_lines.append('    ' + line.lstrip())
        else:
            fixed_lines.append('')

fixed_function = '\n'.join(fixed_lines)

# Создаем новый контент с правильно расположенной функцией
# Находим место для вставки - после всех импортов и глобальных переменных, но до других функций
lines_before = before_function.split('\n')
insert_index = 0

# Ищем последний import или глобальную переменную перед функциями
for i, line in enumerate(lines_before):
    if line.strip().startswith('def '):
        insert_index = i
        break

if insert_index == 0:
    insert_index = len(lines_before)

# Вставляем функцию
new_lines = lines_before[:insert_index] + ['', fixed_function] + lines_before[insert_index:] + [after_function]
new_content = '\n'.join(new_lines)

# Убираем лишние пустые строки
new_content = re.sub(r'\n\s*\n\s*\n', '\n\n', new_content)

# Сохраняем
with open('/home/ais/shared/horseAI/web/upload_lameness_fixed_final.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Создан исправленный файл")

# Проверяем синтаксис
import subprocess
result = subprocess.run(
    ["python3", "-m", "py_compile", "/home/ais/shared/horseAI/web/upload_lameness_fixed_final.py"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Синтаксис правильный")
    # Заменяем оригинальный файл
    import shutil
    shutil.move('/home/ais/shared/horseAI/web/upload_lameness_fixed_final.py', '/home/ais/shared/horseAI/web/upload_lameness.py')
    print("✅ Файл заменен")
else:
    print(f"❌ Ошибка синтаксиса: {result.stderr[:200]}")
