"""
ML Views для обработки видео - фронтенд часть
"""
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.conf import settings

from web.database.models import Animal, User as CustomUser
import requests
import sys
import subprocess
import threading
import os
from datetime import datetime
from web.database.models import Animal, Video, Analysis, CustomUser

# Добавьте эту функцию для запуска вашего детектора
def run_final_detector(video_path, video_id, animal_id, user_id):
    """
    Запускает final_real_detector_correct.py
    """
    try:
        print(f"\n🚀 ЗАПУСК ВАШЕГО ДЕТЕКТОРА")
        print(f"   Видео: {video_path}")
        
        # Папка для результатов
        output_dir = os.path.join(settings.MEDIA_ROOT, "ml_results", f"vid_{video_id}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Команда для запуска
        cmd = [
            sys.executable,
            "/home/ais/shared/horseAI/final_real_detector_correct.py",
            "--video", video_path,
            "--output", output_dir,
            "--video-id", str(video_id)
        ]
        
        print(f"   Команда: {' '.join(cmd)}")
        
        # Запускаем
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd="/home/ais/shared/horseAI"
        )
        
        print(f"✅ Детектор завершен. Код: {result.returncode}")
        
        if result.returncode == 0:
            return {
                'success': True,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'output_dir': output_dir
            }
        else:
            return {
                'success': False,
                'error': f"Код ошибки: {result.returncode}",
                'stderr': result.stderr
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }



@csrf_exempt
@login_required
def upload_video_for_analysis(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST метод'})
    
    try:
        print("\n" + "="*60)
        print("📥 ЗАГРУЗКА ВИДЕО ДЛЯ АНАЛИЗА")
        print("="*60)
        
        # Получаем файл
        video_file = request.FILES.get('video_file')
        animal_id = request.POST.get('animal_id')
        
        if not video_file:
            return JsonResponse({'success': False, 'error': 'Выберите видео'})
        
        print(f"📹 Видео: {video_file.name}")
        print(f"🐴 ID животного: {animal_id}")
        
        # Сохраняем видео
        import uuid
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4()[:8]}_{video_file.name}"
        media_dir = os.path.join(settings.MEDIA_ROOT, "ml_videos")
        os.makedirs(media_dir, exist_ok=True)
        
        filepath = os.path.join(media_dir, filename)
        
        with open(filepath, 'wb+') as f:
            for chunk in video_file.chunks():
                f.write(chunk)
        
        print(f"✅ Видео сохранено: {filepath}")
        
        # Находим пользователя
        custom_user = CustomUser.objects.get(login=request.user.username)
        
        # Находим или создаем животное
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
            file_path=f'ml_videos/{filename}',
            upload_date=datetime.now(),
            analysis_status='processing'
        )
        
        print(f"✅ Видео в БД: ID={video.video_id}")
        
        # СОЗДАЕМ ЗАДАЧУ ДЛЯ ВАШЕГО ДЕТЕКТОРА
        task_id = str(uuid.uuid4())
        
        # Сохраняем задачу в глобальный словарь
        if not hasattr(upload_video_for_analysis, 'tasks'):
            upload_video_for_analysis.tasks = {}
        
        upload_video_for_analysis.tasks[task_id] = {
            'status': 'processing',
            'video_id': video.video_id,
            'video_path': filepath,
            'animal_id': animal.animal_id,
            'user_id': request.user.username,
            'start_time': datetime.now().isoformat()
        }
        
        # Запускаем детектор в фоне
        def run_detector_in_background():
            try:
                print(f"🔬 Запускаем ваш детектор для видео ID {video.video_id}")
                
                # Запускаем ВАШ детектор
                result = run_final_detector(
                    filepath,
                    video.video_id,
                    animal.animal_id,
                    request.user.username
                )
                
                if result['success']:
                    # Парсим результат
                    detector_result = parse_detector_result(result['output_dir'], result['stdout'])
                    
                    # Обновляем статус видео
                    video.analysis_status = 'completed'
                    video.save()
                    
                    # Создаем анализ в БД
                    analysis = Analysis.objects.create(
                        video=video,
                        posture='normal',
                        is_lame=detector_result.get('is_lame', False),
                        lameness_probability=detector_result.get('lameness_probability', 0),
                        lameness_confidence=detector_result.get('confidence', 50.0),
                        diagnosis=detector_result.get('diagnosis', 'Анализ выполнен'),
                        analysis_date=datetime.now()
                    )
                    
                    upload_video_for_analysis.tasks[task_id]['status'] = 'completed'
                    upload_video_for_analysis.tasks[task_id]['analysis_id'] = analysis.analysis_id
                    upload_video_for_analysis.tasks[task_id]['result'] = detector_result
                    
                    print(f"✅ Анализ сохранен: ID={analysis.analysis_id}")
                    
                else:
                    # Ошибка
                    video.analysis_status = 'failed'
                    video.save()
                    
                    Analysis.objects.create(
                        video=video,
                        diagnosis='Ошибка анализа',
                        diagnosis_note=result.get('error', 'Неизвестная ошибка'),
                        analysis_date=datetime.now()
                    )
                    
                    upload_video_for_analysis.tasks[task_id]['status'] = 'failed'
                    upload_video_for_analysis.tasks[task_id]['error'] = result.get('error')
                    
                    print(f"❌ Ошибка детектора: {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ Ошибка в фоновом задании: {e}")
                import traceback
                traceback.print_exc()
                
                video.analysis_status = 'failed'
                video.save()
                
                upload_video_for_analysis.tasks[task_id]['status'] = 'failed'
                upload_video_for_analysis.tasks[task_id]['error'] = str(e)
        
        # Запускаем в потоке
        thread = threading.Thread(target=run_detector_in_background)
        thread.daemon = True
        thread.start()
        
        print(f"✅ Задача запущена: {task_id}")
        print("="*60)
        
        # Возвращаем ответ
        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'video_id': video.video_id,
            'message': 'Видео загружено. AI-анализ запущен.',
            'status_url': f'/api/ml/status/{task_id}/'
        })
        
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required
def get_analysis_status(request, task_id):
    """
    Проверка статуса анализа
    """
    # Проверяем есть ли задача
    if not hasattr(upload_video_for_analysis, 'tasks'):
        return JsonResponse({
            'success': False,
            'error': 'Задача не найдена'
        })
    
    if task_id not in upload_video_for_analysis.tasks:
        return JsonResponse({
            'success': False,
            'error': 'Задача не найдена'
        })
    
    task = upload_video_for_analysis.tasks[task_id]
    
    response = {
        'success': True,
        'task_id': task_id,
        'status': task['status'],
        'video_id': task.get('video_id'),
        'start_time': task.get('start_time')
    }
    
    # Добавляем результат если есть
    if task['status'] == 'completed':
        response['analysis_id'] = task.get('analysis_id')
        response['result'] = task.get('result')
        response['message'] = 'Анализ завершен'
        
    elif task['status'] == 'failed':
        response['error'] = task.get('error', 'Неизвестная ошибка')
        response['message'] = 'Ошибка анализа'
    
    return JsonResponse(response)


@csrf_exempt
@login_required
def save_analysis_result(request):
    """Прокси для сохранения результата анализа"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        csrf_token = request.COOKIES.get('csrftoken', '')
        
        api_url = f"http://{request.get_host()}/api/ml/save-result/"
        
        response = requests.post(
            api_url,
            json=json.loads(request.body),
            cookies={'csrftoken': csrf_token, 'sessionid': request.COOKIES.get('sessionid', '')},
            headers={'X-CSRFToken': csrf_token}
        )
        
        return JsonResponse(response.json())
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка сохранения результата: {str(e)}'
        }, status=500)

@login_required
def get_video_analysis(request, video_id):
    """Прокси для получения анализа видео"""
    try:
        csrf_token = request.COOKIES.get('csrftoken', '')
        
        api_url = f"http://{request.get_host()}/api/ml/video/{video_id}/analysis/"
        
        response = requests.get(
            api_url,
            cookies={'csrftoken': csrf_token, 'sessionid': request.COOKIES.get('sessionid', '')},
            headers={'X-CSRFToken': csrf_token}
        )
        
        return JsonResponse(response.json())
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка получения анализа: {str(e)}'
        }, status=500)

@login_required
def get_animal_analyses(request, animal_id):
    """Прокси для получения всех анализов животного"""
    try:
        csrf_token = request.COOKIES.get('csrftoken', '')
        
        api_url = f"http://{request.get_host()}/api/ml/animal/{animal_id}/analyses/"
        
        response = requests.get(
            api_url,
            cookies={'csrftoken': csrf_token, 'sessionid': request.COOKIES.get('sessionid', '')},
            headers={'X-CSRFToken': csrf_token}
        )
        
        return JsonResponse(response.json())
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка получения анализов: {str(e)}'
        }, status=500)

# HTML views
@login_required
def video_upload_page(request):
    """Страница загрузки видео"""
    # Получаем животных пользователя
    try:
        custom_user = CustomUser.objects.get(login=request.user.username)
        animals = Animal.objects.filter(user=custom_user).order_by('name')
    except CustomUser.DoesNotExist:
        animals = []
    
    return render(request, 'frontend/video_upload.html', {
        'animals': animals
    })

@login_required
def analysis_results_page(request):
    """Страница результатов анализа"""
    return render(request, 'frontend/analysis_results.html', {})

@login_required
def analysis_detail_page(request, analysis_id):
    """Страница деталей анализа"""
    return render(request, 'frontend/analysis_detail.html', {
        'analysis_id': analysis_id
    })



def parse_detector_result(output_dir, stdout):
    """
    Парсит результат вашего детектора
    """
    import re
    import json
    from pathlib import Path
    
    result = {
        'is_lame': False,
        'lameness_probability': 0.0,
        'diagnosis': 'Не определено',
        'confidence': 0.0
    }
    
    # Ищем JSON файл
    output_path = Path(output_dir)
    json_files = list(output_path.glob("*real_result.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result.update(data)
                print(f"✅ Прочитан JSON результат из {json_file}")
                break
        except:
            continue
    
    # Если JSON не нашли, парсим stdout
    if result['diagnosis'] == 'Не определено' and stdout:
        # Ищем JSON в stdout
        json_match = re.search(r'===JSON_START===\s*(.*?)\s*===JSON_END===', stdout, re.DOTALL)
        if json_match:
            try:
                json_data = json.loads(json_match.group(1))
                result.update(json_data)
                print("✅ Прочитан JSON из STDOUT")
            except:
                pass
        
        # Парсим текстовый вывод
        if 'хромота' in stdout.lower() or 'lame' in stdout.lower():
            result['is_lame'] = True
            result['diagnosis'] = 'Хромота'
        elif 'норм' in stdout.lower() or 'здор' in stdout.lower():
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
