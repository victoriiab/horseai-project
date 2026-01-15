# /home/ais/shared/horseAI/web/real_final_api.py
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

# Хранилище статусов
_analyses = {}

@csrf_exempt
def upload_video_real_final(request):
    """Использует ИСПРАВЛЕННЫЙ реальный детектор"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Только POST'}, status=400)
    
    if 'video' not in request.FILES:
        return JsonResponse({'error': 'Нет видео файла'}, status=400)
    
    video_file = request.FILES['video']
    
    if video_file.size > 100 * 1024 * 1024:
        return JsonResponse({'error': 'Файл слишком большой (макс 100MB)'}, status=400)
    
    # Создаем уникальный ID
    video_id = str(uuid.uuid4())
    
    # Сохраняем видео
    video_dir = Path('media') / 'real_videos'
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
    
    # Запускаем ИСПРАВЛЕННЫЙ детектор
    thread = threading.Thread(target=run_real_final_detector, args=(video_id,))
    thread.daemon = True
    thread.start()
    
    return JsonResponse({
        'success': True,
        'video_id': video_id,
        'video_name': video_file.name,
        'message': 'Видео загружено. Запущен РЕАЛЬНЫЙ анализ.'
    })

def run_real_final_detector(video_id):
    """Запускает исправленный реальный детектор"""
    try:
        analysis = _analyses[video_id]
        analysis['status'] = 'processing'
        
        video_path = Path(analysis['video_path'])
        
        # Создаем output директорию
        output_dir = Path('media') / 'real_output' / video_id
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Используем ИСПРАВЛЕННЫЙ детектор
        cmd = [
            'python', '/home/ais/shared/horseAI/final_real_detector_real.py',
            '--video', str(video_path),
            '--output', str(output_dir)
        ]
        
        analysis['progress'] = 20
        analysis['message'] = 'Запуск DLC анализа...'
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=600)  # 10 минут
        
        # Обновляем прогресс
        analysis['progress'] = 80
        analysis['message'] = 'Обработка результатов...'
        
        # Парсим JSON результат
        if '===JSON_START===' in stdout:
            json_start = stdout.find('===JSON_START===') + len('===JSON_START===')
            json_end = stdout.find('===JSON_END===')
            json_str = stdout[json_start:json_end].strip()
            
            result = json.loads(json_str)
            
            # Проверяем успешность
            if 'is_lame' in result:  # Успешный анализ
                analysis['status'] = 'completed'
                analysis['progress'] = 100
                analysis['message'] = 'Анализ завершен'
                
                # Форматируем результат для фронтенда
                formatted_result = format_real_result(result, video_id, analysis['video_name'])
                
                # Сохраняем размеченное видео если есть
                if result.get('labeled_video'):
                    save_real_video(video_id, result['labeled_video'], output_dir)
                    formatted_result['annotated_video_url'] = f'/api/lameness/real/download/{video_id}/'
                
                analysis['result'] = formatted_result
                
            else:  # Ошибка
                analysis['status'] = 'failed'
                analysis['error'] = result.get('error', 'Неизвестная ошибка')
                
        else:
            analysis['status'] = 'failed'
            analysis['error'] = 'Детектор не вернул результаты'
            print(f"stdout:\n{stdout[:500]}")
            print(f"stderr:\n{stderr[:500]}")
            
    except subprocess.TimeoutExpired:
        analysis['status'] = 'failed'
        analysis['error'] = 'Таймаут анализа (10 минут)'
        
    except Exception as e:
        analysis['status'] = 'failed'
        analysis['error'] = str(e)
        
    finally:
        analysis['end_time'] = time.time()
        analysis['processing_time'] = analysis['end_time'] - analysis['start_time']

def format_real_result(result, video_id, video_name):
    """Форматирует реальный результат для фронтенда"""
    # Переводим диагноз на русский
    diagnosis_ru = {
        'Probably lame': 'Вероятно хромая',
        'Probably healthy': 'Вероятно здоровая', 
        'Lame': 'Хромая',
        'Healthy': 'Здоровая',
        'Uncertain result': 'Неопределенный результат'
    }
    
    diagnosis_note_ru = {
        '(recommend examination)': '(рекомендуется осмотр)',
        '(high confidence)': '(высокая уверенность)',
        '(low confidence)': '(низкая уверенность)'
    }
    
    diagnosis = result.get('diagnosis', 'Не определен')
    diagnosis_note = result.get('diagnosis_note', '')
    
    return {
        'success': True,
        'is_lame': result.get('is_lame', False),
        'lameness_probability': result.get('lameness_probability', 0),
        'confidence': result.get('confidence', 0),
        'diagnosis': diagnosis_ru.get(diagnosis, diagnosis),
        'diagnosis_note': diagnosis_note_ru.get(diagnosis_note, diagnosis_note),
        'threshold_used': result.get('threshold_used', 0.5),
        'features': result.get('features', {}),
        'video_id': video_id,
        'video_name': video_name,
        'processing_time_seconds': result.get('processing_time', 0),
        'h5_file': result.get('h5_file'),
        'labeled_video': result.get('labeled_video')
    }

def save_real_video(video_id, video_name, output_dir):
    """Сохраняет размеченное видео"""
    try:
        # Ищем видео файл
        if video_name and Path(video_name).exists():
            video_path = Path(video_name)
        else:
            # Ищем в output директории
            video_files = list(output_dir.glob("*.mp4"))
            if not video_files:
                return False
            
            video_path = video_files[0]
        
        # Копируем в медиа
        media_dir = Path('media') / 'annotated_videos'
        media_dir.mkdir(exist_ok=True, parents=True)
        
        annotated_path = media_dir / f"{video_id}_annotated.mp4"
        shutil.copy2(video_path, annotated_path)
        
        return True
        
    except Exception as e:
        print(f"Ошибка сохранения видео: {e}")
        return False

def get_status_real_final(request, video_id):
    """Получение статуса реального анализа"""
    if video_id not in _analyses:
        return JsonResponse({'status': 'not_found'}, status=404)
    
    analysis = _analyses[video_id]
    
    response_data = {
        'status': analysis['status'],
        'progress': analysis.get('progress', 0),
        'message': analysis.get('message', ''),
        'video_name': analysis.get('video_name', '')
    }
    
    if 'start_time' in analysis:
        elapsed = time.time() - analysis['start_time']
        response_data['elapsed_seconds'] = round(elapsed, 2)
    
    if analysis['status'] == 'completed' and analysis.get('result'):
        response_data.update(analysis['result'])
    
    if analysis['status'] == 'failed' and analysis.get('error'):
        response_data['error'] = analysis['error']
    
    return JsonResponse(response_data)

def download_annotated_real_final(request, video_id):
    """Скачивание реального размеченного видео"""
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
        video_dir = Path(analysis['video_path']).parent.parent / 'real_output' / video_id
        if video_dir.exists():
            video_files = list(video_dir.glob("*.mp4"))
            if video_files:
                video_file = video_files[0]
    
    if not video_file or not video_file.exists():
        return JsonResponse({'error': 'Размеченное видео не найдено'}, status=404)
    
    try:
        with open(video_file, 'rb') as f:
            response = HttpResponse(f.read(), content_type='video/mp4')
            response['Content-Disposition'] = f'attachment; filename="{video_id}_annotated.mp4"'
            return response
    except Exception as e:
        return JsonResponse({'error': f'Ошибка чтения файла: {str(e)}'}, status=500)
