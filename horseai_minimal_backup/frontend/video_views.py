"""
Views для загрузки и обработки видео
"""
import os
import sys

# Добавляем путь к ml_processing в Python path
sys.path.insert(0, '/home/ais/shared/horseAI')

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.conf import settings
import uuid
from datetime import datetime
import json

from web.database.models import User as CustomUser, Animal, Video, Analysis

# Импортируем очередь обработки
try:
    from ml_processing.processing_queue import get_processing_queue
    PROCESSING_AVAILABLE = True
    print("✅ Модуль ml_processing загружен успешно")
except ImportError as e:
    print(f"⚠️ Ошибка импорта ml_processing: {e}")
    PROCESSING_AVAILABLE = False

@csrf_exempt
@login_required
def api_upload_video(request):
    """
    API для загрузки видео и запуска анализа
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST метод'}, status=405)
    
    print(f"\n{'='*60}")
    print("🚀 API ЗАГРУЗКИ ВИДЕО")
    print(f"   Пользователь: {request.user.username}")
    print(f"   Время: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    
    try:
        # 1. Проверяем файл
        video_file = request.FILES.get('video_file')
        if not video_file:
            print("❌ Нет файла видео")
            return JsonResponse({'success': False, 'error': 'Выберите видеофайл'}, status=400)
        
        # 2. Проверяем животное
        animal_id = request.POST.get('animal_id', '').strip()
        if not animal_id:
            print("❌ Нет ID животного")
            return JsonResponse({'success': False, 'error': 'Выберите животное'}, status=400)
        
        print(f"📹 Видео файл: {video_file.name} ({video_file.size} bytes)")
        print(f"🐴 Animal ID из формы: '{animal_id}'")
        
        # 3. Находим пользователя
        try:
            custom_user = CustomUser.objects.get(login=request.user.username)
            print(f"✅ Пользователь найден: {custom_user.login}")
        except CustomUser.DoesNotExist:
            print("❌ Пользователь не найден в БД")
            return JsonResponse({'success': False, 'error': 'Пользователь не найден'}, status=400)
        
        # 4. Находим или создаем животное
        animal = None
        try:
            # Пробуем как число
            animal_id_int = int(animal_id)
            print(f"   Пробуем найти животное по числовому ID: {animal_id_int}")
            animal = Animal.objects.get(animal_id=animal_id_int, user=custom_user)
            print(f"✅ Животное найдено: {animal.name} (ID: {animal.animal_id})")
        except ValueError:
            # Не число - ищем по имени или создаем
            print(f"⚠️ Animal ID '{animal_id}' не число")
            
            existing = Animal.objects.filter(user=custom_user, name__icontains=animal_id).first()
            if existing:
                animal = existing
                print(f"✅ Животное найдено по имени: {animal.name}")
            else:
                # Создаем новое животное
                animal = Animal.objects.create(
                    user=custom_user,
                    name=f'Лошадь {animal_id}',
                    sex='M',
                    age=5,
                    estimated_weight=500.0,
                    created_at=datetime.now()
                )
                print(f"✅ Создано новое животное: {animal.name}")
        except Animal.DoesNotExist:
            print(f"⚠️ Животное ID {animal_id} не найдено, создаем новое")
            animal = Animal.objects.create(
                user=custom_user,
                name=f'Лошадь {animal_id}',
                sex='M',
                age=5,
                estimated_weight=500.0,
                created_at=datetime.now()
            )
            print(f"✅ Создано новое животное: {animal.name}")
        
        # 5. Сохраняем видео файл
        # Создаем уникальное имя
        safe_name = str(uuid.uuid4())[:8] + '_' + video_file.name.replace(' ', '_')
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}"
        
        # Папка для видео
        media_dir = os.path.join(settings.MEDIA_ROOT, "videos")
        os.makedirs(media_dir, exist_ok=True)
        
        filepath = os.path.join(media_dir, filename)
        
        # Сохраняем файл
        with open(filepath, 'wb+') as f:
            for chunk in video_file.chunks():
                f.write(chunk)
        
        print(f"✅ Видео сохранено: {filepath}")
        
        # 6. Создаем запись в БД
        video = Video.objects.create(
            animal=animal,
            user=custom_user,
            file_path=f'videos/{filename}',
            upload_date=datetime.now(),
            duration=0,
            resolution='unknown',
            analysis_status='queued'
        )
        
        print(f"✅ Запись видео создана в БД: ID={video.video_id}")
        
        # 7. Добавляем в очередь обработки (если доступна)
        if PROCESSING_AVAILABLE:
            try:
                processing_queue = get_processing_queue()
                processing_queue.add_task(
                    video_id=video.video_id,
                    video_path=filepath,
                    animal_id=animal.animal_id
                )
                print(f"✅ Видео добавлено в очередь обработки")
                queue_status = 'queued'
            except Exception as e:
                print(f"⚠️ Ошибка добавления в очередь: {e}")
                video.analysis_status = 'failed'
                video.save()
                return JsonResponse({
                    'success': False,
                    'error': f'Ошибка очереди: {str(e)}',
                    'video_id': video.video_id
                }, status=500)
        else:
            print(f"⚠️ Очередь обработки недоступна")
            video.analysis_status = 'processing_offline'
            video.save()
            queue_status = 'processing_offline'
        
        # 8. Возвращаем ответ
        response_data = {
            'success': True,
            'message': 'Видео загружено и поставлено в очередь на анализ',
            'video_id': video.video_id,
            'animal_id': animal.animal_id,
            'animal_name': animal.name,
            'status': queue_status,
            'status_url': f'/api/video/status/{video.video_id}/',
            'estimated_time': '5-30 минут',
            'redirect_url': f'/analysis/status/{video.video_id}/'
        }
        
        print(f"📤 Отправляем ответ: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        print(f"{'='*60}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"💥 Критическая ошибка в API: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def api_video_status(request, video_id):
    """
    API для проверки статуса обработки видео
    """
    try:
        # Проверяем права доступа
        custom_user = CustomUser.objects.get(login=request.user.username)
        video = get_object_or_404(Video, video_id=video_id, user=custom_user)
        
        # Инициализируем базовый ответ
        response_data = {
            'success': True,
            'video_id': video_id,
            'db_status': video.analysis_status,
            'animal_name': video.animal.name if video.animal else 'Неизвестно'
        }
        
        # Получаем статус из очереди если доступна
        if PROCESSING_AVAILABLE:
            try:
                processing_queue = get_processing_queue()
                queue_status = processing_queue.get_status(video_id)
                result = processing_queue.get_result(video_id)
                
                response_data.update({
                    'status': queue_status.get('status', 'unknown'),
                    'queue_status': queue_status,
                    'result': result
                })
                
                # Обновляем статус в БД если изменился
                if queue_status.get('status') != video.analysis_status:
                    video.analysis_status = queue_status.get('status', 'unknown')
                    video.save()
                    response_data['db_status'] = video.analysis_status
                
                # Если анализ завершен, создаем/обновляем запись Analysis
                if result and result.get('success') and queue_status.get('status') == 'completed':
                    analysis, created = Analysis.objects.update_or_create(
                        video=video,
                        defaults={
                            'posture': 'normal',
                            'gait_quality': 'poor' if result.get('is_lame') else 'good',
                            'size_category': 'large',
                            'estimated_weight': video.animal.estimated_weight or 500.0,
                            'confidence_score': result.get('confidence', 50.0) / 100.0,
                            'analysis_date': datetime.now(),
                            'is_lame': result.get('is_lame', False),
                            'lameness_probability': result.get('lameness_probability', 0),
                            'lameness_confidence': result.get('confidence', 50.0),
                            'diagnosis': result.get('diagnosis', 'Анализ выполнен'),
                            'diagnosis_note': result.get('diagnosis_note', ''),
                            'analysis_video_path': result.get('h5_file', '')
                        }
                    )
                    
                    response_data['analysis_id'] = analysis.analysis_id
                    response_data['analysis_created'] = created
                    
            except Exception as e:
                print(f"⚠️ Ошибка получения статуса из очереди: {e}")
                response_data['queue_error'] = str(e)
        else:
            response_data['queue_status'] = 'processing_queue_unavailable'
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'video_id': video_id,
            'status': 'error'
        }, status=500)

@login_required 
def analysis_status_page(request, video_id):
    """
    Страница статуса анализа
    """
    try:
        custom_user = CustomUser.objects.get(login=request.user.username)
        video = get_object_or_404(Video, video_id=video_id, user=custom_user)
        
        context = {
            'video': video,
            'video_id': video_id,
            'animal_name': video.animal.name if video.animal else 'Неизвестно',
            'upload_date': video.upload_date,
            'status': video.analysis_status
        }
        
        return render(request, 'frontend/analysis_status.html', context)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=404)

@login_required
def api_queue_stats(request):
    """
    Статистика очереди (для админов)
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
    
    try:
        if not PROCESSING_AVAILABLE:
            return JsonResponse({
                'success': False,
                'error': 'Очередь обработки недоступна',
                'timestamp': datetime.now().isoformat()
            }, status=503)
        
        processing_queue = get_processing_queue()
        stats = processing_queue.get_queue_stats()
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
