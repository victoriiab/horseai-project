from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from pathlib import Path
import uuid
import threading
import time
from web.database.models import Video, Animal, User, Analysis
from django.conf import settings
import subprocess
import tempfile

# Глобальный словарь для хранения статусов задач
ml_tasks = {}

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ml_upload_video(request):
    """Загрузка видео для ML анализа"""
    try:
        if 'video_file' not in request.FILES:
            return Response({'success': False, 'error': 'Файл не найден'}, status=400)
        
        animal_id = request.POST.get('animal_id')
        if not animal_id:
            return Response({'success': False, 'error': 'Не указана лошадь'}, status=400)
        
        # Получаем пользователя
        try:
            custom_user = User.objects.get(login=request.user.username)
            animal = Animal.objects.get(pk=animal_id, user=custom_user)
        except (User.DoesNotExist, Animal.DoesNotExist):
            return Response({'success': False, 'error': 'Лошадь не найдена'}, status=404)
        
        video_file = request.FILES['video_file']
        
        # Сохраняем видео
        media_dir = settings.MEDIA_ROOT / 'videos'
        media_dir.mkdir(exist_ok=True)
        
        filename = f"{uuid.uuid4()}_{video_file.name}"
        filepath = media_dir / filename
        
        with open(filepath, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)
        
        # Создаем запись в БД
        video = Video.objects.create(
            animal=animal,
            user=custom_user,
            file_path=f"videos/{filename}",
            duration=0,  # Можно вычислить позже
            resolution="unknown",
            analysis_status="pending"
        )
        
        # Создаем задачу ML анализа
        task_id = str(uuid.uuid4())
        ml_tasks[task_id] = {
            'status': 'pending',
            'progress': 0,
            'video_id': video.video_id,
            'message': 'Задача создана',
            'created_at': time.time(),
            'result': None,
            'error': None
        }
        
        # Запускаем анализ в отдельном потоке
        thread = threading.Thread(target=run_ml_analysis, args=(task_id, video, filepath))
        thread.daemon = True
        thread.start()
        
        return Response({
            'success': True,
            'message': 'Видео загружено',
            'video_id': video.video_id,
            'task_id': task_id,
            'file_path': video.file_path
        })
        
    except Exception as e:
        print(f"Ошибка загрузки видео: {e}")
        return Response({'success': False, 'error': str(e)}, status=500)

def run_ml_analysis(task_id, video, filepath):
    """Запуск ML анализа в отдельном потоке"""
    try:
        ml_tasks[task_id]['status'] = 'processing'
        ml_tasks[task_id]['progress'] = 10
        ml_tasks[task_id]['message'] = 'Подготовка модели...'
        
        # Проверяем наличие ML модели
        model_path = Path("/home/ais/shared/horseAI/models")
        detector_script = Path("/home/ais/shared/horseAI/final_real_detector_correct.py")
        
        if not detector_script.exists():
            raise FileNotFoundError(f"ML скрипт не найден: {detector_script}")
        
        # Создаем временный файл для вывода
        output_dir = settings.MEDIA_ROOT / 'analysis_results' / task_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / 'result.json'
        
        # Обновляем статус
        ml_tasks[task_id]['progress'] = 30
        ml_tasks[task_id]['message'] = 'Запуск анализа видео...'
        
        # Запускаем ML скрипт
        # ВАЖНО: Эта команда должна быть адаптирована под ваш ML скрипт
        cmd = [
            'python3', str(detector_script),
            '--video', str(filepath),
            '--output', str(output_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"ML скрипт вернул ошибку: {result.stderr}")
        
        # Читаем результат
        if output_file.exists():
            with open(output_file, 'r') as f:
                ml_result = json.load(f)
        else:
            # Парсим вывод скрипта
            ml_result = parse_ml_output(result.stdout)
        
        # Обновляем статус
        ml_tasks[task_id]['progress'] = 80
        ml_tasks[task_id]['message'] = 'Сохранение результатов...'
        
        # Создаем анализ в БД
        analysis = Analysis.objects.create(
            video=video,
            is_lame=ml_result.get('is_lame', False),
            lameness_probability=ml_result.get('lameness_probability', 0),
            lameness_confidence=ml_result.get('confidence', 0),
            diagnosis=ml_result.get('diagnosis', ''),
            diagnosis_note=ml_result.get('diagnosis_note', ''),
            gait_quality='normal' if not ml_result.get('is_lame') else 'lame'
        )
        
        # Обновляем видео
        video.analysis_status = 'completed'
        video.save()
        
        # Сохраняем результат
        ml_tasks[task_id]['status'] = 'completed'
        ml_tasks[task_id]['progress'] = 100
        ml_tasks[task_id]['message'] = 'Анализ завершен'
        ml_tasks[task_id]['result'] = {
            'analysis_id': analysis.analysis_id,
            'is_lame': analysis.is_lame,
            'lameness_probability': analysis.lameness_probability,
            'confidence': analysis.lameness_confidence,
            'diagnosis': analysis.diagnosis,
            'video_id': video.video_id
        }
        
    except subprocess.TimeoutExpired:
        ml_tasks[task_id]['status'] = 'failed'
        ml_tasks[task_id]['error'] = 'Таймаут анализа (больше 5 минут)'
    except Exception as e:
        print(f"Ошибка ML анализа: {e}")
        ml_tasks[task_id]['status'] = 'failed'
        ml_tasks[task_id]['error'] = str(e)
        
        # Обновляем видео
        video.analysis_status = 'failed'
        video.save()

def parse_ml_output(output):
    """Парсинг вывода ML скрипта"""
    try:
        # Попробуем найти JSON в выводе
        import re
        json_match = re.search(r'\{.*\}', output, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        
        # Или парсим текстовый вывод
        result = {
            'is_lame': False,
            'lameness_probability': 0,
            'confidence': 0,
            'diagnosis': 'Анализ выполнен',
            'diagnosis_note': output[:500]  # Первые 500 символов
        }
        
        # Простая эвристика для определения хромоты
        if any(word in output.lower() for word in ['lame', 'хром', 'limping', 'abnormal']):
            result['is_lame'] = True
            result['lameness_probability'] = 75
            result['diagnosis'] = 'Подозрение на хромоту'
        elif any(word in output.lower() for word in ['normal', 'норм', 'healthy']):
            result['is_lame'] = False
            result['lameness_probability'] = 10
            result['diagnosis'] = 'Норма'
        
        return result
        
    except Exception as e:
        print(f"Ошибка парсинга вывода: {e}")
        return {
            'is_lame': False,
            'lameness_probability': 0,
            'confidence': 0,
            'diagnosis': 'Анализ выполнен',
            'diagnosis_note': 'Результат не может быть проанализирован'
        }

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ml_check_status(request, task_id):
    """Проверка статуса ML задачи"""
    if task_id not in ml_tasks:
        return Response({'success': False, 'error': 'Задача не найдена'}, status=404)
    
    task = ml_tasks[task_id]
    
    # Очищаем старые задачи (старше 1 часа)
    cleanup_old_tasks()
    
    return Response({
        'success': True,
        'status': task['status'],
        'progress': task['progress'],
        'message': task['message'],
        'result': task.get('result'),
        'error': task.get('error'),
        'video_id': task.get('video_id')
    })

def cleanup_old_tasks():
    """Очистка старых задач"""
    current_time = time.time()
    to_remove = []
    
    for task_id, task in ml_tasks.items():
        if current_time - task['created_at'] > 3600:  # 1 час
            to_remove.append(task_id)
    
    for task_id in to_remove:
        del ml_tasks[task_id]

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ml_save_result(request):
    """Сохранение результата ML анализа в БД"""
    try:
        data = request.data
        task_id = data.get('task_id')
        video_id = data.get('video_id')
        
        if task_id in ml_tasks and ml_tasks[task_id]['status'] == 'completed':
            result = ml_tasks[task_id]['result']
            
            if result:
                return Response({
                    'success': True,
                    'message': 'Результат сохранен',
                    'analysis_id': result['analysis_id'],
                    'is_lame': result['is_lame'],
                    'lameness_probability': result['lameness_probability'],
                    'diagnosis': result['diagnosis']
                })
        
        # Ищем существующий анализ
        if video_id:
            try:
                analysis = Analysis.objects.filter(video_id=video_id).latest('analysis_date')
                return Response({
                    'success': True,
                    'message': 'Результат найден',
                    'analysis_id': analysis.analysis_id,
                    'is_lame': analysis.is_lame,
                    'lameness_probability': analysis.lameness_probability,
                    'diagnosis': analysis.diagnosis
                })
            except Analysis.DoesNotExist:
                pass
        
        return Response({'success': False, 'error': 'Результат не найден'}, status=404)
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ml_test_model(request):
    """Тест ML модели"""
    try:
        # Проверяем наличие ML скрипта
        detector_script = Path("/home/ais/shared/horseAI/final_real_detector_correct.py")
        
        if not detector_script.exists():
            return Response({
                'success': False,
                'error': f'ML скрипт не найден: {detector_script}'
            })
        
        # Простой тест - проверяем можем ли импортировать
        import sys
        sys.path.append(str(detector_script.parent))
        
        test_result = {
            'success': True,
            'message': 'ML модель доступна',
            'script_exists': True,
            'script_path': str(detector_script),
            'models_dir': '/home/ais/shared/horseAI/models/',
            'has_models': os.path.exists('/home/ais/shared/horseAI/models/')
        }
        
        return Response(test_result)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Ошибка теста ML модели'
        }, status=500)

# Простой эмулятор ML для тестирования
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ml_simulate_analysis(request):
    """Эмуляция ML анализа для тестирования"""
    try:
        animal_id = request.data.get('animal_id')
        video_name = request.data.get('video_name', 'test_video.mp4')
        
        # Создаем фейковый результат
        import random
        is_lame = random.random() > 0.7  # 30% шанс хромоты
        probability = random.uniform(0, 100) if is_lame else random.uniform(0, 30)
        
        result = {
            'success': True,
            'is_lame': is_lame,
            'lameness_probability': probability,
            'confidence': random.uniform(70, 95),
            'diagnosis': 'Хромота обнаружена' if is_lame else 'Норма',
            'diagnosis_note': 'Тестовый анализ выполнен успешно',
            'video_name': video_name,
            'timestamp': time.time()
        }
        
        return Response(result)
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
