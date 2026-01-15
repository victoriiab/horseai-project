import json
import subprocess
import threading
import time
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import uuid
import os

# Путь к нашему детектору
DETECTOR_SCRIPT = Path("/home/ais/shared/horseAI/final_real_detector.py")

# Хранилище статусов анализа
analysis_status = {}

def run_detector_background(video_id: str, video_path: Path):
    """Запуск детектора в фоновом режиме"""
    try:
        # Команда для запуска детектора
        cmd = [
            "python",
            str(DETECTOR_SCRIPT),
            video_id,
            str(video_path)
        ]
        
        print(f"🚀 Запускаем детектор: {' '.join(cmd)}")
        
        # Запускаем процесс
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 минут
            env={**os.environ, 'PYTHONPATH': '/home/ais/shared/horseAI:' + os.environ.get('PYTHONPATH', '')}
        )
        
        # Парсим результат
        output = result.stdout
        import re
        json_match = re.search(r'🎯 JSON результат для API:\s*(\{.*\})', output, re.DOTALL)
        
        if json_match:
            result_data = json.loads(json_match.group(1))
            analysis_status[video_id] = {
                'status': 'completed',
                'result': result_data,
                'stdout': output[-1000:]
            }
        else:
            analysis_status[video_id] = {
                'status': 'failed',
                'error': 'Не удалось получить результат',
                'stdout': output[-1000:],
                'stderr': result.stderr[-500:]
            }
            
    except subprocess.TimeoutExpired:
        analysis_status[video_id] = {
            'status': 'timeout',
            'error': 'Анализ занял слишком много времени'
        }
    except Exception as e:
        analysis_status[video_id] = {
            'status': 'failed',
            'error': str(e)
        }

@csrf_exempt
@require_POST
def start_lameness_analysis(request):
    """Запуск анализа хромоты"""
    try:
        # Получаем видео файл
        video_file = request.FILES.get('video')
        if not video_file:
            return JsonResponse({'error': 'Файл видео не загружен'}, status=400)
        
        # Создаем уникальный ID
        video_id = str(uuid.uuid4())[:8]
        
        # Сохраняем видео во временную папку
        upload_dir = Path("/home/ais/shared/horseAI/media/uploads/lameness")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        video_path = upload_dir / f"{video_id}_{video_file.name}"
        
        with open(video_path, 'wb') as f:
            for chunk in video_file.chunks():
                f.write(chunk)
        
        # Инициализируем статус
        analysis_status[video_id] = {
            'status': 'processing',
            'start_time': time.time(),
            'video_name': video_file.name
        }
        
        # Запускаем анализ в фоне
        thread = threading.Thread(
            target=run_detector_background,
            args=(video_id, video_path)
        )
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'success': True,
            'video_id': video_id,
            'message': 'Анализ хромоты запущен',
            'check_status_url': f'/api/lameness/status/{video_id}/'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def check_analysis_status(request, video_id):
    """Проверка статуса анализа"""
    if video_id not in analysis_status:
        return JsonResponse({'status': 'not_found'}, status=404)
    
    status_data = analysis_status[video_id].copy()
    
    # Добавляем время выполнения если идет обработка
    if status_data['status'] == 'processing':
        elapsed = time.time() - status_data['start_time']
        status_data['elapsed_seconds'] = round(elapsed, 2)
    
    return JsonResponse(status_data)

@csrf_exempt
def test_detector(request):
    """Тестовая endpoint для проверки детектора"""
    try:
        # Тестовое видео
        test_video = Path("/home/ais/shared/horseAI/test/test_videos/healthy_20_mirrored_hhFES5M.mp4")
        
        if not test_video.exists():
            return JsonResponse({'error': 'Тестовое видео не найдено'}, status=404)
        
        video_id = "test_" + str(int(time.time()))[-6:]
        
        # Запускаем детектор
        cmd = [
            "python",
            str(DETECTOR_SCRIPT),
            video_id,
            str(test_video)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Пытаемся извлечь JSON
        import re
        json_match = re.search(r'🎯 JSON результат для API:\s*(\{.*\})', result.stdout, re.DOTALL)
        
        if json_match:
            test_result = json.loads(json_match.group(1))
            return JsonResponse({
                'success': True,
                'test_result': test_result,
                'stdout_preview': result.stdout[:500] + '...' if len(result.stdout) > 500 else result.stdout
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Не удалось получить результат',
                'stdout': result.stdout[-1000:],
                'stderr': result.stderr[-500:]
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def lameness_test_page(request):
    """Страница для тестирования анализа хромоты"""
    from django.shortcuts import render
    return render(request, 'lameness_test.html')
