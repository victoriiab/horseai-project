import os
import json
import subprocess
import tempfile
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage

@login_required
def video_upload_page(request):
    """Страница загрузки видео"""
    return render(request, 'frontend/video_upload.html')

@login_required
@csrf_exempt
def analyze_video_api(request):
    """API endpoint для анализа видео"""
    if request.method == 'POST':
        try:
            # Проверяем, есть ли видео файл
            if 'video' not in request.FILES:
                return JsonResponse({'error': 'Не загружено видео'}, status=400)
            
            video_file = request.FILES['video']
            
            # Сохраняем видео временно
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_videos'))
            filename = fs.save(video_file.name, video_file)
            video_path = fs.path(filename)
            
            # ID видео
            video_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.splitext(filename)[0]}"
            
            # Запускаем анализ
            detector_path = '/home/ais/shared/horseAI/final_real_detector_correct.py'
            
            try:
                # Выполняем анализ
                result = subprocess.run(
                    ['python', detector_path, '--video', video_path, '--video-id', video_id],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 минут таймаут
                )
                
                # Получаем вывод
                output = result.stdout
                
                # Ищем JSON в выводе
                if '===JSON_START===' in output:
                    json_str = output.split('===JSON_START===')[1].split('===JSON_END===')[0].strip()
                    result_data = json.loads(json_str)
                else:
                    return JsonResponse({
                        'error': 'Не удалось получить результат анализа',
                        'output': output[:500]  # Первые 500 символов вывода
                    }, status=500)
                
                # Возвращаем успешный результат
                return JsonResponse({
                    'success': True,
                    'result': result_data,
                    'video_id': video_id,
                    'filename': filename
                })
                
            except subprocess.TimeoutExpired:
                return JsonResponse({'error': 'Таймаут анализа (больше 5 минут)'}, status=500)
                
            except Exception as e:
                return JsonResponse({'error': f'Ошибка при анализе: {str(e)}'}, status=500)
                
        except Exception as e:
            return JsonResponse({'error': f'Ошибка сервера: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Неверный метод запроса'}, status=400)

@login_required
def analysis_results_page(request):
    """Страница результатов анализа"""
    # Здесь можно показывать историю анализов
    return render(request, 'frontend/analysis.html')
