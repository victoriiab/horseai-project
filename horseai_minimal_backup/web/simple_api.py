# /home/ais/shared/horseAI/web/simple_api.py
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

# Импортируем ваш детектор напрямую
sys.path.insert(0, '/home/ais/shared/horseAI/horseai_project/ml_model/test/test')

# Хранилище статусов
_analyses = {}

@csrf_exempt
def upload_video_direct(request):
    """Прямой вызов вашего детектора"""
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
    video_dir = Path('media') / 'direct_videos'
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
    
    # Запускаем через командную строку - это самый надежный способ!
    thread = threading.Thread(target=run_via_cli, args=(video_id,))
    thread.daemon = True
    thread.start()
    
    return JsonResponse({
        'success': True,
        'video_id': video_id,
        'video_name': video_file.name,
        'message': 'Видео загружено. Анализ запущен.'
    })

def run_via_cli(video_id):
    """Запускает анализ через командную строку"""
    try:
        analysis = _analyses[video_id]
        analysis['status'] = 'processing'
        
        video_path = Path(analysis['video_path'])
        
        # Создаем output директорию
        output_dir = Path('media') / 'direct_output' / video_id
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Используем ваш скрипт final_real_detector_real.py
        # Он уже умеет работать с моделью
        cmd = [
            'python', '/home/ais/shared/horseAI/final_real_detector_real.py',
            '--video', str(video_path),
            '--output', str(output_dir)
        ]
        
        analysis['progress'] = 30
        analysis['message'] = 'Запуск анализа DLC...'
        
        # Запускаем процесс
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Ждем завершения с таймаутом
        try:
            stdout, stderr = process.communicate(timeout=300)  # 5 минут
            
            analysis['progress'] = 70
            analysis['message'] = 'Обработка результатов...'
            
            # Парсим JSON результат
            if '===JSON_START===' in stdout:
                json_start = stdout.find('===JSON_START===') + len('===JSON_START===')
                json_end = stdout.find('===JSON_END===')
                json_str = stdout[json_start:json_end].strip()
                
                try:
                    result = json.loads(json_str)
                    
                    if result.get('status') == 'completed' or 'is_lame' in result:
                        # Успешный анализ
                        analysis['status'] = 'completed'
                        analysis['progress'] = 100
                        analysis['message'] = 'Анализ завершен'
                        analysis['result'] = result
                        
                        # Добавляем URL для скачивания если есть видео
                        if 'labeled_video' in result and result['labeled_video']:
                            # Находим видео файл
                            video_files = list(output_dir.glob("*labeled*.mp4")) + \
                                         list(output_dir.glob("*_sk.mp4"))
                            
                            if video_files:
                                # Копируем в медиа
                                media_dir = Path('media') / 'annotated_videos'
                                media_dir.mkdir(exist_ok=True, parents=True)
                                
                                annotated_path = media_dir / f"{video_id}_annotated.mp4"
                                shutil.copy2(video_files[0], annotated_path)
                                
                                result['annotated_video_url'] = f'/api/lameness/direct/download/{video_id}/'
                                
                    else:
                        # Ошибка
                        analysis['status'] = 'failed'
                        analysis['error'] = result.get('error', 'Неизвестная ошибка')
                        analysis['message'] = f'Ошибка анализа: {analysis["error"]}'
                        
                except json.JSONDecodeError as e:
                    analysis['status'] = 'failed'
                    analysis['error'] = f'Ошибка парсинга JSON: {e}'
                    analysis['message'] = analysis['error']
                    
            else:
                # Не нашли JSON
                analysis['status'] = 'failed'
                analysis['error'] = 'Детектор не вернул результаты'
                analysis['message'] = analysis['error']
                print(f"stdout:\n{stdout[:500]}")
                print(f"stderr:\n{stderr[:500]}")
                
        except subprocess.TimeoutExpired:
            process.kill()
            analysis['status'] = 'failed'
            analysis['error'] = 'Таймаут анализа (5 минут)'
            analysis['message'] = 'Анализ превысил лимит времени'
            
    except Exception as e:
        analysis['status'] = 'failed'
        analysis['error'] = str(e)
        analysis['message'] = f'Ошибка: {str(e)}'
        
    finally:
        # Обновляем время окончания
        analysis['end_time'] = time.time()
        analysis['processing_time'] = analysis['end_time'] - analysis['start_time']

def get_status_direct(request, video_id):
    """Получение статуса прямого анализа"""
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
        result = analysis['result']
        
        # Форматируем для фронтенда
        response_data.update({
            'success': True,
            'is_lame': result.get('is_lame', False),
            'lameness_probability': result.get('lameness_probability', 0),
            'confidence': result.get('confidence', 0),
            'diagnosis': result.get('diagnosis', 'Не определен'),
            'diagnosis_note': result.get('diagnosis_note', ''),
            'features': result.get('features', {}),
            'processing_time_seconds': round(analysis.get('processing_time', 0), 2)
        })
        
        if 'annotated_video_url' in result:
            response_data['annotated_video_url'] = result['annotated_video_url']
    
    # Если есть ошибка, добавляем ее
    if analysis['status'] == 'failed' and analysis.get('error'):
        response_data['error'] = analysis['error']
    
    return JsonResponse(response_data)

def download_annotated_direct(request, video_id):
    """Скачивание размеченного видео"""
    if video_id not in _analyses:
        return JsonResponse({'error': 'Видео не найдено'}, status=404)
    
    analysis = _analyses[video_id]
    
    if analysis['status'] != 'completed':
        return JsonResponse({'error': 'Анализ не завершен'}, status=404)
    
    # Пробуем найти видео
    video_file = None
    
    # Сначала в медиа
    media_file = Path('media') / 'annotated_videos' / f"{video_id}_annotated.mp4"
    if media_file.exists():
        video_file = media_file
    else:
        # Пробуем в output директории
        if 'video_path' in analysis:
            video_dir = Path(analysis['video_path']).parent.parent / 'direct_output' / video_id
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
