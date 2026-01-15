"""
Views для ML обработки видео
"""
import os
import json
import uuid
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.conf import settings

from web.database.models import Video, Animal, Analysis, User as CustomUser
from ml_processing.ml_integrator import process_video, get_processing_status

@csrf_exempt
@login_required
def upload_video_for_analysis(request):
    """Загрузка видео для ML анализа"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Получаем данные
        animal_id = request.POST.get('animal_id')
        video_file = request.FILES.get('video_file')
        
        if not animal_id or not video_file:
            return JsonResponse({
                'success': False,
                'error': 'Не указано животное или видео'
            }, status=400)
        
        # Проверяем животное
        custom_user = CustomUser.objects.get(login=request.user.username)
        animal = get_object_or_404(Animal, animal_id=animal_id, user=custom_user)
        
        # Сохраняем видео
        video_dir = settings.MEDIA_ROOT / 'videos' / str(animal_id)
        video_dir.mkdir(parents=True, exist_ok=True)
        
        video_filename = f"{uuid.uuid4()}_{video_file.name}"
        video_path = video_dir / video_filename
        
        with open(video_path, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)
        
        # Создаем запись в БД
        video = Video.objects.create(
            animal=animal,
            user=custom_user,
            file_path=str(video_path.relative_to(settings.MEDIA_ROOT)),
            upload_date=datetime.now(),
            duration=0,  # TODO: извлечь длительность
            resolution='unknown',
            analysis_status='pending'
        )
        
        # Добавляем на ML обработку
        task_id = process_video(str(video_path), animal_id, custom_user.user_id)
        
        # Обновляем запись видео
        video.analysis_status = 'processing'
        video.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Видео загружено и отправлено на анализ',
            'video_id': video.video_id,
            'task_id': task_id,
            'video_path': video.file_path
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка загрузки видео: {str(e)}'
        }, status=500)

@login_required
def get_analysis_status(request, task_id):
    """Получение статуса анализа"""
    try:
        status = get_processing_status(task_id)
        
        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'status': status.get('status', 'unknown'),
            'message': status.get('message', ''),
            'progress': status.get('progress', 0),
            'result': status.get('result', None) if 'result' in status else None,
            'error': status.get('error', None) if 'error' in status else None
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка получения статуса: {str(e)}'
        }, status=500)

@csrf_exempt
@login_required
def save_analysis_result(request):
    """Сохранение результата анализа в БД"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        video_id = data.get('video_id')
        task_id = data.get('task_id')
        
        if not video_id or not task_id:
            return JsonResponse({
                'success': False,
                'error': 'Не указаны video_id или task_id'
            }, status=400)
        
        # Получаем статус задачи
        status = get_processing_status(task_id)
        
        if status['status'] != 'completed':
            return JsonResponse({
                'success': False,
                'error': 'Анализ еще не завершен'
            }, status=400)
        
        # Получаем видео
        video = get_object_or_404(Video, video_id=video_id)
        
        # Проверяем права
        custom_user = CustomUser.objects.get(login=request.user.username)
        if video.user.user_id != custom_user.user_id:
            return JsonResponse({
                'success': False,
                'error': 'Нет доступа к этому видео'
            }, status=403)
        
        result = status.get('result', {})
        
        # Создаем или обновляем анализ
        analysis, created = Analysis.objects.update_or_create(
            video=video,
            defaults={
                'posture': 'стоя',  # TODO: определить из анализа
                'gait_quality': 'хорошая' if not result.get('is_lame') else 'плохая',
                'size_category': 'средний',  # TODO: определить
                'estimated_weight': video.animal.estimated_weight,
                'confidence_score': result.get('confidence', 0),
                'analysis_date': datetime.now(),
                'is_lame': result.get('is_lame', False),
                'lameness_probability': result.get('lameness_probability', 0),
                'lameness_confidence': result.get('confidence', 0),
                'diagnosis': result.get('diagnosis', ''),
                'diagnosis_note': result.get('diagnosis_note', ''),
                'analysis_video_path': ''  # TODO: сохранить аннотированное видео
            }
        )
        
        # Обновляем статус видео
        video.analysis_status = 'completed'
        video.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Результат анализа сохранен',
            'analysis_id': analysis.analysis_id,
            'is_lame': analysis.is_lame,
            'lameness_probability': analysis.lameness_probability,
            'diagnosis': analysis.diagnosis
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка сохранения результата: {str(e)}'
        }, status=500)

@login_required
def get_video_analysis(request, video_id):
    """Получение результата анализа видео"""
    try:
        video = get_object_or_404(Video, video_id=video_id)
        
        # Проверяем права
        custom_user = CustomUser.objects.get(login=request.user.username)
        if video.user.user_id != custom_user.user_id:
            return JsonResponse({
                'success': False,
                'error': 'Нет доступа к этому видео'
            }, status=403)
        
        # Получаем анализ если есть
        try:
            analysis = Analysis.objects.get(video=video)
            
            return JsonResponse({
                'success': True,
                'analysis': {
                    'analysis_id': analysis.analysis_id,
                    'video_id': video.video_id,
                    'animal_id': video.animal.animal_id,
                    'animal_name': video.animal.name,
                    'is_lame': analysis.is_lame,
                    'lameness_probability': analysis.lameness_probability,
                    'lameness_confidence': analysis.lameness_confidence,
                    'diagnosis': analysis.diagnosis,
                    'diagnosis_note': analysis.diagnosis_note,
                    'confidence_score': analysis.confidence_score,
                    'analysis_date': analysis.analysis_date.isoformat() if analysis.analysis_date else None,
                    'gait_quality': analysis.gait_quality,
                    'posture': analysis.posture,
                    'analysis_video_path': analysis.analysis_video_path
                },
                'video': {
                    'video_id': video.video_id,
                    'file_path': video.file_path,
                    'upload_date': video.upload_date.isoformat() if video.upload_date else None,
                    'duration': video.duration,
                    'resolution': video.resolution,
                    'analysis_status': video.analysis_status
                }
            })
            
        except Analysis.DoesNotExist:
            return JsonResponse({
                'success': True,
                'analysis': None,
                'message': 'Анализ еще не выполнен',
                'video': {
                    'video_id': video.video_id,
                    'analysis_status': video.analysis_status
                }
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка получения анализа: {str(e)}'
        }, status=500)

@login_required
def get_animal_analyses(request, animal_id):
    """Получение всех анализов животного"""
    try:
        custom_user = CustomUser.objects.get(login=request.user.username)
        animal = get_object_or_404(Animal, animal_id=animal_id, user=custom_user)
        
        videos = Video.objects.filter(animal=animal).order_by('-upload_date')
        
        analyses = []
        for video in videos:
            try:
                analysis = Analysis.objects.get(video=video)
                analyses.append({
                    'analysis_id': analysis.analysis_id,
                    'video_id': video.video_id,
                    'upload_date': video.upload_date.isoformat() if video.upload_date else None,
                    'is_lame': analysis.is_lame,
                    'lameness_probability': analysis.lameness_probability,
                    'diagnosis': analysis.diagnosis,
                    'analysis_date': analysis.analysis_date.isoformat() if analysis.analysis_date else None,
                    'gait_quality': analysis.gait_quality,
                    'confidence_score': analysis.confidence_score
                })
            except Analysis.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'animal_id': animal_id,
            'animal_name': animal.name,
            'analyses': analyses,
            'total': len(analyses)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка получения анализов: {str(e)}'
        }, status=500)
