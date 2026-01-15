"""
РЕАЛЬНЫЙ API для вашего детектора хромоты.
Просто запускает final_real_detector_correct.py через subprocess.
"""
import os
import sys
import json
import subprocess
import threading
import uuid
import tempfile
from pathlib import Path
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from web.database.models import Animal, Video, Analysis, CustomUser

# Глобальный словарь для хранения статусов задач
TASK_STATUS = {}

def run_detector_task(video_path, task_id, animal_id, user_id):
    """
    Запускает ваш детектор в фоновом режиме
    """
    try:
        print(f"🚀 Запуск детектора для задачи {task_id}")
        
        # Создаем папку для результатов
        output_dir = Path(settings.MEDIA_ROOT) / "detector_results" / task_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Команда для запуска вашего детектора
        cmd = [
            sys.executable,
            "/home/ais/shared/horseAI/final_real_detector_correct.py",
            "--video", str(video_path),
            "--output", str(output_dir),
            "--video-id", task_id
        ]
        
        print(f"🔧 Команда: {' '.join(cmd)}")
        
        # Запускаем детектор
        start_time = datetime.now()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 минут максимум
            cwd="/home/ais/shared/horseAI"
        )
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Детектор завершен за {elapsed:.1f} сек")
        print(f"Код возврата: {result.returncode}")
        
        # Обновляем статус
        TASK_STATUS[task_id]['status'] = 'completed'
        TASK_STATUS[task_id]['returncode'] = result.returncode
        TASK_STATUS[task_id]['stdout'] = result.stdout[:2000]
        TASK_STATUS[task_id]['stderr'] = result.stderr[:2000]
        TASK_STATUS[task_id]['elapsed'] = elapsed
        
        # Парсим результат
        if result.returncode == 0:
            # Ищем JSON файл с результатами
            result_file = output_dir / f"{task_id}_real_result.json"
            if result_file.exists():
                with open(result_file, 'r', encoding='utf-8') as f:
                    detector_result = json.load(f)
            else:
                # Пытаемся парсить stdout
                detector_result = parse_stdout(result.stdout)
            
            # Сохраняем результат в БД
            save_analysis_to_db(detector_result, task_id, animal_id, user_id, output_dir)
            
            TASK_STATUS[task_id]['result'] = detector_result
            TASK_STATUS[task_id]['success'] = True
        else:
            TASK_STATUS[task_id]['success'] = False
            TASK_STATUS[task_id]['error'] = f"Детектор вернул код {result.returncode}: {result.stderr[:200]}"
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Таймаут детектора (10 минут)")
        TASK_STATUS[task_id]['status'] = 'failed'
        TASK_STATUS[task_id]['success'] = False
        TASK_STATUS[task_id]['error'] = 'Таймаут анализа (10 минут)'
        
    except Exception as e:
        print(f"❌ Ошибка в задаче: {e}")
        import traceback
        traceback.print_exc()
        TASK_STATUS[task_id]['status'] = 'failed'
        TASK_STATUS[task_id]['success'] = False
        TASK_STATUS[task_id]['error'] = str(e)

def parse_stdout(stdout):
    """
    Парсит stdout вашего детектора
    """
    import re
    
    result = {
        'is_lame': False,
        'lameness_probability': 0.0,
        'diagnosis': 'Не определено',
        'confidence': 0.0
    }
    
    # Ищем JSON в stdout
    json_match = re.search(r'===JSON_START===\s*(.*?)\s*===JSON_END===', stdout, re.DOTALL)
    if json_match:
        try:
            json_data = json.loads(json_match.group(1))
            return json_data
        except:
            pass
    
    # Парсим текстовый вывод
    stdout_lower = stdout.lower()
    
    # Диагноз
    if 'хромота' in stdout_lower or 'lame' in stdout_lower:
        result['is_lame'] = True
        result['diagnosis'] = 'Хромота'
    elif 'норм' in stdout_lower or 'здор' in stdout_lower:
        result['is_lame'] = False
        result['diagnosis'] = 'Норма'
    
    # Вероятность
    prob_match = re.search(r'Вероятность хромоты:\s*([\d.]+)%', stdout)
    if prob_match:
        result['lameness_probability'] = float(prob_match.group(1))
    
    # Уверенность
    conf_match = re.search(r'Уровень уверенности анализа:\s*([\d.]+)%', stdout)
    if conf_match:
        result['confidence'] = float(conf_match.group(1))
    
    return result

def save_analysis_to_db(detector_result, task_id, animal_id, user_id, output_dir):
    """
    Сохраняет результат анализа в БД
    """
    try:
        # Находим пользователя
        custom_user = CustomUser.objects.get(login=user_id)
        
        # Находим или создаем животное
        animal = None
        try:
            animal_id_int = int(animal_id)
            animal = Animal.objects.get(animal_id=animal_id_int, user=custom_user)
        except:
            animal = Animal.objects.create(
                user=custom_user,
                name=f'Лошадь {animal_id}',
                sex='M',
                age=5,
                estimated_weight=500.0,
                created_at=datetime.now()
            )
        
        # Создаем запись видео
        video = Video.objects.create(
            animal=animal,
            user=custom_user,
            file_path=TASK_STATUS[task_id]['video_path'],
            upload_date=datetime.now(),
            analysis_status='completed' if detector_result.get('status') == 'completed' else 'failed'
        )
        
        # Создаем анализ
        analysis = Analysis.objects.create(
            video=video,
            posture='normal',
            gait_quality='good' if not detector_result.get('is_lame') else 'poor',
            size_category='large',
            estimated_weight=animal.estimated_weight or 500.0,
            confidence_score=detector_result.get('confidence', 50.0) / 100.0,
            analysis_date=datetime.now(),
            is_lame=detector_result.get('is_lame', False),
            lameness_probability=detector_result.get('lameness_probability', 0),
            lameness_confidence=detector_result.get('confidence', 50.0),
            diagnosis=detector_result.get('diagnosis', 'Анализ выполнен'),
            diagnosis_note=detector_result.get('diagnosis_note', '')[:500]
        )
        
        print(f"✅ Анализ сохранен в БД: ID={analysis.analysis_id}")
        TASK_STATUS[task_id]['analysis_id'] = analysis.analysis_id
        
    except Exception as e:
        print(f"⚠️ Ошибка сохранения в БД: {e}")

@csrf_exempt
@login_required
def api_analyze_video(request):
    """
    РЕАЛЬНЫЙ API для анализа видео вашим детектором
    POST /api/detector/analyze/
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST метод'}, status=405)
    
    try:
        print("\n" + "="*80)
        print("🚀 API ЗАПРОС НА АНАЛИЗ ВИДЕО")
        print("="*80)
        
        # Проверяем аутентификацию
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Требуется вход'}, status=401)
        
        # Получаем данные
        video_file = request.FILES.get('video_file')
        animal_id = request.POST.get('animal_id', '1')
        
        if not video_file:
            return JsonResponse({'success': False, 'error': 'Выберите видеофайл'})
        
        print(f"📹 Видео: {video_file.name}")
        print(f"👤 Пользователь: {request.user.username}")
        print(f"🐴 ID животного: {animal_id}")
        
        # Сохраняем видео
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4()[:8]}_{video_file.name}"
        media_dir = Path(settings.MEDIA_ROOT) / "detector_videos"
        media_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = media_dir / filename
        
        with open(filepath, 'wb+') as f:
            for chunk in video_file.chunks():
                f.write(chunk)
        
        print(f"✅ Видео сохранено: {filepath}")
        
        # Создаем задачу
        task_id = str(uuid.uuid4())[:8]
        
        TASK_STATUS[task_id] = {
            'status': 'processing',
            'start_time': datetime.now().isoformat(),
            'video_name': video_file.name,
            'video_path': f"detector_videos/{filename}",
            'user': request.user.username,
            'animal_id': animal_id,
            'progress': 0,
            'result': None,
            'error': None,
            'success': None
        }
        
        # Запускаем детектор в фоновом потоке
        thread = threading.Thread(
            target=run_detector_task,
            args=(str(filepath), task_id, animal_id, request.user.username)
        )
        thread.daemon = True
        thread.start()
        
        print(f"✅ Задача запущена: {task_id}")
        print("="*80)
        
        # Возвращаем ответ с ID задачи
        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'message': 'Видео загружено. Анализ запущен.',
            'status_url': f'/api/detector/status/{task_id}/',
            'estimated_time': '2-5 минут'
        })
        
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
def api_get_analysis_status(request, video_id):
    """
    Получение статуса анализа
    GET /api/detector/status/<video_id>/
    """
    if video_id not in TASK_STATUS:
        return JsonResponse({
            'success': False,
            'error': 'Задача не найдена'
        }, status=404)
    
    task_data = TASK_STATUS[video_id]
    
    response = {
        'success': True,
        'task_id': video_id,
        'status': task_data['status'],
        'progress': task_data.get('progress', 0),
        'video_name': task_data['video_name'],
        'start_time': task_data['start_time']
    }
    
    # Добавляем результат если есть
    if task_data['status'] == 'completed':
        response['result'] = task_data.get('result')
        response['analysis_id'] = task_data.get('analysis_id')
        response['success'] = task_data.get('success', False)
        
    elif task_data['status'] == 'failed':
        response['error'] = task_data.get('error', 'Неизвестная ошибка')
        response['success'] = False
    
    return JsonResponse(response)

@csrf_exempt
def api_test_detector(request):
    """
    Тестовый endpoint для проверки работы детектора
    GET /api/detector/test/
    """
    # Проверяем доступность детектора
    detector_path = Path("/home/ais/shared/horseAI/final_real_detector_correct.py")
    
    if not detector_path.exists():
        return JsonResponse({
            'success': False,
            'error': f'Детектор не найден: {detector_path}'
        })
    
    # Проверяем можно ли запустить
    try:
        result = subprocess.run(
            [sys.executable, str(detector_path), "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return JsonResponse({
            'success': True,
            'detector_status': 'available',
            'help_output': result.stdout[:500],
            'path': str(detector_path)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка запуска детектора: {e}'
        })
