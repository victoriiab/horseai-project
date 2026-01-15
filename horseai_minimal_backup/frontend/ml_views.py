# /home/ais/shared/horseAI/frontend/ml_views.py
import json
import uuid
import threading
from datetime import datetime
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from web.database.models import Animal, Video, Analysis, LamenessAnalysis
from web.horse_detector import HorseLamenessDetector, extract_features
import pandas as pd

# Хранилище задач
task_storage = {}
detector_instance = None

def get_detector():
    """Получаем или создаем экземпляр детектора"""
    global detector_instance
    if detector_instance is None:
        try:
            detector_instance = HorseLamenessDetector()
            print("✅ ML детектор инициализирован")
        except Exception as e:
            print(f"❌ Ошибка инициализации детектора: {e}")
            detector_instance = None
    return detector_instance

@login_required
def video_upload_page(request):
    """Страница загрузки видео"""
    animals = Animal.objects.filter(user=request.user)
    return render(request, 'frontend/video_upload.html', {'animals': animals})

@login_required
def analysis_results_page(request):
    """Страница результатов анализа"""
    analyses = Analysis.objects.filter(video__animal__user=request.user).order_by('-analysis_date')
    return render(request, 'frontend/analysis_results.html', {'analyses': analyses})

@login_required
def analysis_detail_page(request, analysis_id):
    """Детальная страница анализа"""
    analysis = get_object_or_404(Analysis, analysis_id=analysis_id, video__animal__user=request.user)
    return render(request, 'frontend/analysis_detail.html', {'analysis': analysis})

@csrf_exempt
@login_required
def upload_video_for_analysis(request):
    """API для загрузки видео (вызывается из интерфейса)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
    
    try:
        # Проверяем наличие файла
        if 'video_file' not in request.FILES:
            return JsonResponse({'error': 'Файл видео не найден'}, status=400)
        
        animal_id = request.POST.get('animal_id')
        if not animal_id:
            return JsonResponse({'error': 'ID животного не указан'}, status=400)
        
        # Получаем животное
        try:
            animal = Animal.objects.get(animal_id=animal_id, user=request.user)
        except Animal.DoesNotExist:
            return JsonResponse({'error': 'Животное не найдено'}, status=404)
        
        # Сохраняем видео
        video_file = request.FILES['video_file']
        fs = FileSystemStorage(location=settings.MEDIA_ROOT / 'videos')
        filename = fs.save(video_file.name, video_file)
        video_path = fs.path(filename)
        
        # Создаем запись в БД
        video = Video.objects.create(
            animal=animal,
            user=request.user,
            file_path=str(video_path),
            upload_date=datetime.now(),
            duration=0,
            resolution='unknown',
            analysis_status='pending'
        )
        
        # Создаем задачу анализа
        task_id = str(uuid.uuid4())
        task_storage[task_id] = {
            'status': 'pending',
            'progress': 0,
            'message': 'Задача создана',
            'video_id': video.video_id,
            'video_path': video_path,
            'animal_id': animal_id,
            'user_id': request.user.id,
            'result': None,
            'error': None,
            'created_at': datetime.now()
        }
        
        # Запускаем анализ в фоне
        thread = threading.Thread(
            target=process_video_analysis,
            args=(task_id,)
        )
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'video_id': video.video_id,
            'message': 'Видео загружено, анализ запущен'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def process_video_analysis(task_id):
    """Фоновая обработка видео"""
    try:
        task = task_storage[task_id]
        task['status'] = 'processing'
        task['progress'] = 10
        task['message'] = 'Инициализация ML модели'
        
        # Получаем детектор
        detector = get_detector()
        if not detector:
            raise Exception("ML детектор не доступен")
        
        video_path = Path(task['video_path'])
        
        # Шаг 1: Анализ видео с DLC
        task['progress'] = 20
        task['message'] = 'Анализ позы с помощью DeepLabCut'
        
        h5_file, labeled_video = detector.analyze_video_superanimal(video_path)
        
        if not h5_file or not h5_file.exists():
            raise Exception("Не удалось получить данные поз")
        
        # Шаг 2: Чтение данных и извлечение признаков
        task['progress'] = 40
        task['message'] = 'Извлечение биомеханических признаков'
        
        df = pd.read_hdf(h5_file)
        features = extract_features(df)
        
        if features is None:
            raise Exception("Не удалось извлечь признаки из видео")
        
        # Шаг 3: Предсказание хромоты
        task['progress'] = 70
        task['message'] = 'Анализ хромоты'
        
        result = detector.predict_lameness(features)
        
        # Шаг 4: Сохранение результатов
        task['progress'] = 90
        task['message'] = 'Сохранение результатов в БД'
        
        # Обновляем видео
        video = Video.objects.get(video_id=task['video_id'])
        video.analysis_status = 'completed'
        video.save()
        
        # Создаем анализ
        analysis = Analysis.objects.create(
            video=video,
            posture='analyzed',
            gait_quality='lame' if result['is_lame'] else 'normal',
            size_category='adult',
            estimated_weight=None,
            confidence_score=result['confidence'],
            analysis_date=datetime.now(),
            is_lame=result['is_lame'],
            lameness_probability=result['lameness_probability'],
            lameness_confidence=result['confidence'],
            diagnosis=result['diagnosis'],
            diagnosis_note=result['diagnosis_note'],
            analysis_video_path=str(labeled_video) if labeled_video else None
        )
        
        # Также создаем запись в LamenessAnalysis
        LamenessAnalysis.objects.create(
            video=video,
            original_filename=video_path.name,
            uploaded_at=datetime.now(),
            status='completed',
            is_lame=result['is_lame'],
            lameness_probability=result['lameness_probability'],
            confidence=result['confidence'],
            diagnosis=result['diagnosis'],
            diagnosis_note=result['diagnosis_note'],
            annotated_video=str(labeled_video) if labeled_video else None,
            h5_file=str(h5_file)
        )
        
        # Сохраняем результат в task
        task['result'] = {
            'analysis_id': analysis.analysis_id,
            'is_lame': result['is_lame'],
            'lameness_probability': result['lameness_probability'],
            'confidence': result['confidence'],
            'diagnosis': result['diagnosis'],
            'diagnosis_note': result['diagnosis_note'],
            'h5_file': str(h5_file),
            'labeled_video': str(labeled_video) if labeled_video else None
        }
        
        task['status'] = 'completed'
        task['progress'] = 100
        task['message'] = 'Анализ успешно завершен'
        
    except Exception as e:
        task['status'] = 'failed'
        task['error'] = str(e)
        task['message'] = f'Ошибка: {str(e)}'
        print(f"Ошибка в задаче {task_id}: {e}")

@csrf_exempt
@login_required
def get_analysis_status(request, task_id):
    """Проверка статуса задачи"""
    if task_id not in task_storage:
        return JsonResponse({'error': 'Задача не найдена'}, status=404)
    
    task = task_storage[task_id]
    
    # Проверяем права доступа
    if task.get('user_id') != request.user.id:
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    response = {
        'success': True,
        'task_id': task_id,
        'status': task['status'],
        'progress': task['progress'],
        'message': task['message']
    }
    
    if task['status'] == 'completed' and task['result']:
        response['result'] = task['result']
    
    if task['status'] == 'failed':
        response['error'] = task.get('error', 'Неизвестная ошибка')
    
    return JsonResponse(response)

@csrf_exempt
@login_required
def save_analysis_result(request):
    """Сохранение результата (уже делается в фоновой задаче)"""
    return JsonResponse({
        'success': True,
        'message': 'Результаты сохраняются автоматически'
    })

@csrf_exempt
@login_required
def get_video_analysis(request, video_id):
    """Получение анализа по видео"""
    try:
        video = Video.objects.get(video_id=video_id, animal__user=request.user)
        analysis = Analysis.objects.filter(video=video).first()
        
        if not analysis:
            return JsonResponse({'error': 'Анализ не найден'}, status=404)
        
        return JsonResponse({
            'success': True,
            'analysis': {
                'analysis_id': analysis.analysis_id,
                'is_lame': analysis.is_lame,
                'lameness_probability': analysis.lameness_probability,
                'confidence': analysis.lameness_confidence,
                'diagnosis': analysis.diagnosis,
                'diagnosis_note': analysis.diagnosis_note,
                'analysis_date': analysis.analysis_date.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Video.DoesNotExist:
        return JsonResponse({'error': 'Видео не найдено'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_animal_analyses(request, animal_id):
    """Получение всех анализов животного"""
    try:
        animal = Animal.objects.get(animal_id=animal_id, user=request.user)
        analyses = Analysis.objects.filter(video__animal=animal).order_by('-analysis_date')
        
        analyses_list = []
        for analysis in analyses:
            analyses_list.append({
                'analysis_id': analysis.analysis_id,
                'video_id': analysis.video.video_id,
                'is_lame': analysis.is_lame,
                'lameness_probability': analysis.lameness_probability,
                'confidence': analysis.lameness_confidence,
                'diagnosis': analysis.diagnosis,
                'analysis_date': analysis.analysis_date.strftime('%Y-%m-%d %H:%M:%S') if analysis.analysis_date else None
            })
        
        return JsonResponse({
            'success': True,
            'animal_id': animal_id,
            'analyses': analyses_list,
            'count': len(analyses_list)
        })
        
    except Animal.DoesNotExist:
        return JsonResponse({'error': 'Животное не найдено'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Функция для тестирования модели (добавьте в ml_views.py если ее нет)
@csrf_exempt
def test_ml_model_api(request):
    """Тест ML модели"""
    try:
        detector = get_detector()
        if detector:
            return JsonResponse({
                'success': True,
                'message': 'ML модель доступна и готова к работе',
                'model_loaded': True
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'ML модель не загружена',
                'model_loaded': False
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'model_loaded': False
        })
