"""
ПРОСТОЙ API для интеграции детектора
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from datetime import datetime
import os
from pathlib import Path
import uuid

from web.database.models import Animal, Video, Analysis, CustomUser
from .ml_detector import detector

@csrf_exempt
@login_required
def upload_and_analyze_simple(request):
    """
    САМЫЙ ПРОСТОЙ endpoint для загрузки и анализа
    Маленькими шагами!
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False, 
            'error': 'Только POST'
        })
    
    print("\n" + "="*50)
    print("🚀 ЗАПУСК ПРОСТОГО АНАЛИЗА")
    print("="*50)
    
    try:
        # 1. Проверяем файл
        if 'video_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Выберите видео файл'
            })
        
        video_file = request.FILES['video_file']
        animal_id = request.POST.get('animal_id', '1')
        
        print(f"📹 Файл: {video_file.name}, размер: {video_file.size}")
        print(f"🐴 Animal ID: {animal_id}")
        
        # 2. Сохраняем файл
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
            for chunk in video_file.chunks():
                tmp.write(chunk)
            temp_path = tmp.name
        
        print(f"✅ Файл сохранен временно: {temp_path}")
        
        # 3. Быстрый ответ пользователю
        response_data = {
            'success': True,
            'message': 'Видео принято. Начинаем анализ...',
            'video_id': f"temp_{int(time.time())}",
            'status': 'processing'
        }
        
        # 4. Запускаем анализ В ФОНЕ (после отправки ответа)
        import threading
        import time
        
        def analyze_in_background():
            """Фоновая задача анализа"""
            try:
                print(f"\n🔬 ФОНОВЫЙ АНАЛИЗ НАЧАТ")
                start_time = time.time()
                
                # Запускаем детектор
                result = detector.analyze_video(temp_path)
                
                elapsed = time.time() - start_time
                print(f"✅ Анализ завершен за {elapsed:.1f} сек")
                print(f"   Результат: {result}")
                
                # Сохраняем в БД
                save_to_db(request.user.username, video_file.name, result)
                
                # Очищаем временный файл
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
            except Exception as e:
                print(f"❌ Ошибка в фоне: {e}")
        
        # Запускаем фоном
        thread = threading.Thread(target=analyze_in_background)
        thread.daemon = True
        thread.start()
        
        print(f"✅ Фоновая задача запущена")
        print("="*50)
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def save_to_db(username, filename, result):
    """Сохраняем результат в БД"""
    try:
        print(f"💾 Сохраняем в БД...")
        
        # Находим пользователя
        user = CustomUser.objects.get(login=username)
        
        # Создаем животное (упрощенно)
        animal, _ = Animal.objects.get_or_create(
            user=user,
            name=f"Лошадь из {filename}",
            defaults={
                'sex': 'M',
                'age': 5,
                'estimated_weight': 500.0,
                'created_at': datetime.now()
            }
        )
        
        # Создаем видео запись
        video = Video.objects.create(
            animal=animal,
            user=user,
            file_path=f"temp/{filename}",
            upload_date=datetime.now(),
            analysis_status='completed'
        )
        
        # Создаем анализ
        analysis_data = {
            'video': video,
            'analysis_date': datetime.now(),
            'diagnosis': result.get('diagnosis', 'Анализ выполнен'),
            'is_lame': result.get('is_lame', False),
            'lameness_probability': result.get('lameness_probability', 0),
            'confidence_score': result.get('confidence', 50) / 100.0
        }
        
        Analysis.objects.create(**analysis_data)
        
        print(f"✅ Сохранено: животное={animal.name}, видео={video.video_id}")
        
    except Exception as e:
        print(f"⚠️ Ошибка сохранения в БД: {e}")

@csrf_exempt
def test_detector_api(request):
    """Тестовый endpoint для проверки детектора"""
    print("=== ТЕСТ ДЕТЕКТОРА ===")
    
    # Простая проверка
    test_result = detector.test_detector()
    
    return JsonResponse({
        'success': test_result,
        'message': 'Детектор работает' if test_result else 'Детектор не работает',
        'test_time': datetime.now().isoformat()
    })
