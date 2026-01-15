"""
РЕАЛЬНЫЙ API с АВТОМАТИЧЕСКИМ ML анализом
"""

import json
import os
import subprocess
import re
import uuid
import threading
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone

def run_ml_analysis_background(video_id, video_path, animal_name, analysis_id):
    """Фоновая задача REAL ML анализа"""
    print(f"[BG ML] 🧠 Запуск REAL ML анализа для видео {video_id}")
    
    try:
        # 1. Проверяем детектор
        detector = '/home/ais/shared/horseAI/final_real_detector_correct.py'
        if not os.path.exists(detector):
            print("[BG ML] ❌ Детектор не найден")
            return
        
        # 2. Запускаем ML анализ
        ml_id = f"ml_{uuid.uuid4().hex[:8]}"
        cmd = ['python', detector, ml_id, video_path]
        
        print(f"[BG ML] 🚀 Команда: {' '.join(cmd)}")
        start_time = time.time()
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 минут
            cwd='/home/ais/shared/horseAI'
        )
        
        processing_time = time.time() - start_time
        print(f"[BG ML] ✅ Анализ завершен за {processing_time:.1f} сек")
        
        # 3. Парсим результат
        json_match = re.search(r'===JSON_START===\s*(.*?)\s*===JSON_END===', result.stdout, re.DOTALL)
        
        if json_match:
            ml_result = json.loads(json_match.group(1))
            
            # 4. Обновляем БД
            from web.database.models import Analysis
            analysis = Analysis.objects.get(analysis_id=analysis_id)
            
            analysis.is_lame = ml_result.get('is_lame', False)
            analysis.lameness_probability = ml_result.get('lameness_probability', 0)
            analysis.lameness_confidence = ml_result.get('confidence', 0)
            analysis.diagnosis = ml_result.get('diagnosis', 'Не определено')
            analysis.diagnosis_note = ml_result.get('diagnosis_note', '')
            analysis.confidence_score = ml_result.get('confidence', 0) / 100
            analysis.analysis_status = 'completed'
            
            analysis.save()
            
            print(f"[BG ML] 🎉 Анализ {analysis_id} ОБНОВЛЕН с REAL данными!")
            print(f"[BG ML] 📊 Диагноз: {analysis.diagnosis}")
            print(f"[BG ML] 📊 Вероятность: {analysis.lameness_probability}%")
            
        else:
            print("[BG ML] ❌ Не удалось получить JSON")
            
    except Exception as e:
        print(f"[BG ML] ❌ Ошибка: {e}")

@csrf_exempt
@login_required
def api_upload_video_with_ml(request):
    """
    ЗАГРУЗКА ВИДЕО + АВТОМАТИЧЕСКИЙ REAL ML АНАЛИЗ
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST метод'}, status=405)
    
    try:
        print("🚀 НАЧАЛО: Загрузка + REAL ML анализ")
        
        # 1. Проверка
        video_file = request.FILES.get('video_file')
        animal_id = request.POST.get('animal_id', '1')
        
        if not video_file:
            return JsonResponse({'success': False, 'error': 'Файл не выбран'})
        
        # 2. Импортируем
        from web.database.models import Animal, Video, Analysis, User
        
        # 3. Пользователь
        custom_user = User.objects.get(login=request.user.username)
        
        # 4. Животное
        try:
            animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
        except:
            animal = Animal.objects.create(
                user=custom_user,
                name=f'Лошадь {animal_id}',
                sex='M',
                age=5,
                estimated_weight=500.0,
                created_at=timezone.now()
            )
        
        # 5. Сохраняем файл
        filename = f"{uuid.uuid4().hex[:8]}_{video_file.name.replace(' ', '_')}"
        media_dir = '/home/ais/shared/horseAI/media/videos'
        os.makedirs(media_dir, exist_ok=True)
        
        video_path = os.path.join(media_dir, filename)
        
        with open(video_path, 'wb+') as f:
            for chunk in video_file.chunks():
                f.write(chunk)
        
        # 6. Видео в БД
        video = Video.objects.create(
            animal=animal,
            user=custom_user,
            file_path=f'videos/{filename}',
            upload_date=timezone.now(),
            duration=0.0,
            resolution='unknown',
            analysis_status='uploaded'
        )
        
        # 7. Создаем анализ с сообщением об ML анализе
        analysis = Analysis.objects.create(
            video=video,
            posture='analyzing',
            gait_quality='analyzing',
            size_category='analyzing',
            estimated_weight=animal.estimated_weight or 500.0,
            analysis_date=timezone.now(),
            confidence_score=0.0,
            diagnosis='⏳ REAL ML анализ выполняется...',
            is_lame=False,
            lameness_probability=0.0,
            lameness_confidence=0.0
        )
        
        # 8. ЗАПУСКАЕМ REAL ML В ФОНЕ
        ml_thread = threading.Thread(
            target=run_ml_analysis_background,
            args=(video.video_id, video_path, animal.name, analysis.analysis_id),
            daemon=True
        )
        ml_thread.start()
        
        # 9. Возвращаем ответ
        return JsonResponse({
            'success': True,
            'message': '✅ Видео загружено! REAL ML анализ запущен.',
            'note': 'Анализ займет 2-5 минут. Обновите страницу результатов.',
            'video_id': video.video_id,
            'analysis_id': analysis.analysis_id,
            'animal_name': animal.name,
            'ml_status': 'started',
            'estimated_time': '2-5 минут'
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
