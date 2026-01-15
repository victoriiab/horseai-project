# /home/ais/shared/horseAI/web/final_detector_api.py
import sys
import os
import json
import uuid
import tempfile
import subprocess
import time
import threading
import shutil
from pathlib import Path
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Глобальное хранилище
_analyses = {}

@csrf_exempt
def upload_video_final(request):
    """Финальная версия - использует ВАШ реальный детектор"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Только POST'}, status=400)
    
    if 'video' not in request.FILES:
        return JsonResponse({'error': 'Нет видео файла'}, status=400)
    
    video_file = request.FILES['video']
    
    # Проверка размера
    if video_file.size > 100 * 1024 * 1024:
        return JsonResponse({'error': 'Файл слишком большой (макс 100MB)'}, status=400)
    
    # Создаем уникальный ID
    video_id = str(uuid.uuid4())
    
    # Сохраняем видео
    video_dir = Path('media') / 'final_videos'
    video_dir.mkdir(exist_ok=True, parents=True)
    
    video_path = video_dir / f"{video_id}_{video_file.name}"
    
    with open(video_path, 'wb') as f:
        for chunk in video_file.chunks():
            f.write(chunk)
    
    # Инициализируем анализ
    _analyses[video_id] = {
        'status': 'uploaded',
        'video_path': str(video_path),
        'video_name': video_file.name,
        'progress': 0,
        'message': 'Видео загружено',
        'start_time': time.time(),
        'result': None,
        'error': None
    }
    
    # Запускаем анализ в фоне
    thread = threading.Thread(target=run_final_detector, args=(video_id,))
    thread.daemon = True
    thread.start()
    
    return JsonResponse({
        'success': True,
        'video_id': video_id,
        'video_name': video_file.name,
        'message': 'Видео загружено. Запускаем ВАШ реальный анализ.'
    })

def run_final_detector(video_id):
    """Запускает ВАШ финальный детектор"""
    try:
        analysis = _analyses[video_id]
        analysis['status'] = 'processing'
        analysis['progress'] = 10
        analysis['message'] = 'Подготовка...'
        
        video_path = Path(analysis['video_path'])
        
        # Создаем output директорию
        output_dir = Path('media') / 'final_output' / video_id
        output_dir.mkdir(exist_ok=True, parents=True)
        
        analysis['progress'] = 20
        analysis['message'] = 'Запуск ВАШЕГО детектора...'
        
        # Команда для запуска ВАШЕГО детектора
        cmd = [
            'python', '/home/ais/shared/horseAI/final_real_detector_real.py',
            '--video', str(video_path),
            '--output', str(output_dir)
        ]
        
        print(f"Запускаем команду: {' '.join(cmd)}")
        
        # Запускаем процесс
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Читаем вывод в реальном времени
        stdout_lines = []
        stderr_lines = []
        
        def read_output(pipe, lines):
            for line in iter(pipe.readline, ''):
                lines.append(line)
                # Обновляем прогресс на основе вывода
                if 'DLC завершен' in line:
                    analysis['progress'] = 50
                    analysis['message'] = 'DLC анализ завершен'
                elif 'Извлечено' in line and 'признаков' in line:
                    analysis['progress'] = 70
                    analysis['message'] = 'Признаки извлечены'
                elif 'Вероятность хромоты:' in line:
                    analysis['progress'] = 90
                    analysis['message'] = 'Предсказание завершено'
        
        # Запускаем чтение вывода в отдельных потоках
        stdout_thread = threading.Thread(target=read_output, args=(process.stdout, stdout_lines))
        stderr_thread = threading.Thread(target=read_output, args=(process.stderr, stderr_lines))
        
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Ждем завершения
        timeout = 600  # 10 минут
        try:
            process.wait(timeout=timeout)
            
            # Собираем весь вывод
            stdout = ''.join(stdout_lines)
            stderr = ''.join(stderr_lines)
            
            analysis['progress'] = 95
            analysis['message'] = 'Обработка результатов...'
            
            # Парсим результат
            result = parse_detector_output(stdout, stderr, video_id, output_dir)
            
            if result.get('success'):
                analysis['status'] = 'completed'
                analysis['progress'] = 100
                analysis['message'] = 'Анализ завершен'
                analysis['result'] = result
                
                # Сохраняем размеченное видео если есть
                if result.get('labeled_video'):
                    save_annotated_video(video_id, result['labeled_video'], output_dir)
                    result['annotated_video_url'] = f'/api/lameness/final/download/{video_id}/'
                    
            else:
                analysis['status'] = 'failed'
                analysis['error'] = result.get('error', 'Неизвестная ошибка')
                analysis['message'] = f'Ошибка: {analysis["error"]}'
                
        except subprocess.TimeoutExpired:
            process.kill()
            analysis['status'] = 'failed'
            analysis['error'] = f'Таймаут анализа ({timeout} секунд)'
            analysis['message'] = 'Анализ превысил лимит времени'
            
    except Exception as e:
        analysis['status'] = 'failed'
        analysis['error'] = str(e)
        analysis['message'] = f'Ошибка: {str(e)}'
        print(f"Ошибка обработки {video_id}: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Обновляем время окончания
        analysis['end_time'] = time.time()
        analysis['processing_time'] = analysis['end_time'] - analysis['start_time']

def parse_detector_output(stdout, stderr, video_id, output_dir):
    """Парсит вывод детектора и извлекает результат"""
    try:
        # Ищем JSON в выводе
        if '===JSON_START===' in stdout and '===JSON_END===' in stdout:
            json_start = stdout.find('===JSON_START===') + len('===JSON_START===')
            json_end = stdout.find('===JSON_END===')
            json_str = stdout[json_start:json_end].strip()
            
            result = json.loads(json_str)
            result['success'] = True
            
            # Форматируем результат для фронтенда
            if 'is_lame' in result:
                # Уже правильный формат
                return format_for_frontend(result, video_id)
            else:
                # Старый формат, конвертируем
                return convert_to_frontend_format(result, video_id)
                
        else:
            # JSON не найден, создаем ошибку
            return {
                'success': False,
                'error': 'Детектор не вернул результаты в JSON формате',
                'stdout_preview': stdout[:500] if stdout else 'Нет вывода',
                'stderr_preview': stderr[:500] if stderr else 'Нет ошибок'
            }
            
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'Ошибка парсинга JSON: {e}',
            'json_str': json_str[:200] if 'json_str' in locals() else 'Нет JSON'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Ошибка обработки вывода: {e}'
        }

def format_for_frontend(result, video_id):
    """Форматирует результат для фронтенда"""
    return {
        'success': True,
        'is_lame': result.get('is_lame', False),
        'lameness_probability': result.get('lameness_probability', 0),
        'confidence': result.get('confidence', 0),
        'diagnosis': result.get('diagnosis', 'Не определен'),
        'diagnosis_note': result.get('diagnosis_note', ''),
        'threshold_used': result.get('threshold_used', 0.5),
        'features': result.get('features', {}),
        'video_id': video_id,
        'video_name': result.get('video_name', ''),
        'processing_time_seconds': result.get('processing_time', 0),
        'labeled_video': result.get('labeled_video'),
        'h5_file': result.get('h5_file')
    }

def convert_to_frontend_format(result, video_id):
    """Конвертирует старый формат в новый"""
    # Извлекаем данные из старого формата
    if 'test_result' in result:
        # Тестовый формат
        test_result = result['test_result']
        return {
            'success': True,
            'is_lame': test_result.get('is_lame', False),
            'lameness_probability': test_result.get('lameness_probability', 0),
            'confidence': test_result.get('confidence', 0),
            'diagnosis': test_result.get('diagnosis', 'Не определен'),
            'diagnosis_note': test_result.get('diagnosis_note', ''),
            'features': test_result.get('features', {}),
            'video_id': video_id,
            'processing_time_seconds': test_result.get('processing_time_seconds', 0)
        }
    else:
        # Неизвестный формат
        return {
            'success': True,
            'is_lame': False,
            'lameness_probability': 0,
            'confidence': 0,
            'diagnosis': 'Неизвестный формат результата',
            'diagnosis_note': 'Обратитесь к администратору',
            'features': {},
            'video_id': video_id,
            'processing_time_seconds': 0
        }

def save_annotated_video(video_id, video_name, output_dir):
    """Сохраняет размеченное видео в медиа"""
    try:
        # Ищем видео файл
        video_files = list(output_dir.glob(f"*{video_name}"))
        if not video_files:
            # Пробуем другие шаблоны
            video_files = list(output_dir.glob("*labeled*.mp4")) + \
                         list(output_dir.glob("*_sk.mp4")) + \
                         list(output_dir.glob("*.mp4"))
        
        if video_files:
            # Копируем в медиа
            media_dir = Path('media') / 'annotated_videos'
            media_dir.mkdir(exist_ok=True, parents=True)
            
            annotated_path = media_dir / f"{video_id}_annotated.mp4"
            shutil.copy2(video_files[0], annotated_path)
            
            return True
            
    except Exception as e:
        print(f"Ошибка сохранения видео: {e}")
    
    return False

def get_status_final(request, video_id):
    """Получение статуса финального анализа"""
    if video_id not in _analyses:
        return JsonResponse({
            'status': 'not_found',
            'error': 'Анализ не найден'
        }, status=404)
    
    analysis = _analyses[video_id]
    
    response_data = {
        'status': analysis['status'],
        'progress': analysis.get('progress', 0),
        'message': analysis.get('message', ''),
        'video_name': analysis.get('video_name', '')
    }
    
    # Добавляем время
    if 'start_time' in analysis:
        elapsed = time.time() - analysis['start_time']
        response_data['elapsed_seconds'] = round(elapsed, 2)
    
    # Если есть результат, добавляем его
    if analysis['status'] == 'completed' and analysis.get('result'):
        response_data.update(analysis['result'])
    
    # Если есть ошибка, добавляем ее
    if analysis['status'] == 'failed' and analysis.get('error'):
        response_data['error'] = analysis['error']
    
    return JsonResponse(response_data)

def download_annotated_final(request, video_id):
    """Скачивание размеченного видео"""
    if video_id not in _analyses:
        return JsonResponse({'error': 'Видео не найдено'}, status=404)
    
    analysis = _analyses[video_id]
    
    if analysis['status'] != 'completed':
        return JsonResponse({'error': 'Анализ не завершен'}, status=404)
    
    # Ищем видео
    video_file = None
    
    # 1. В медиа
    media_file = Path('media') / 'annotated_videos' / f"{video_id}_annotated.mp4"
    if media_file.exists():
        video_file = media_file
    
    # 2. В output директории
    if not video_file and 'video_path' in analysis:
        video_dir = Path(analysis['video_path']).parent.parent / 'final_output' / video_id
        if video_dir.exists():
            video_files = list(video_dir.glob("*.mp4"))
            if video_files:
                video_file = video_files[0]
    
    if not video_file or not video_file.exists():
        return JsonResponse({'error': 'Размеченное видео не найдено'}, status=404)
    
    # Отдаем файл
    try:
        with open(video_file, 'rb') as f:
            response = HttpResponse(f.read(), content_type='video/mp4')
            response['Content-Disposition'] = f'attachment; filename="{video_id}_annotated.mp4"'
            return response
    except Exception as e:
        return JsonResponse({'error': f'Ошибка чтения файла: {str(e)}'}, status=500)
