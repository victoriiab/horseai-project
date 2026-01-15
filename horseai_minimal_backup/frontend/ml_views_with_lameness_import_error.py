"""
ИСПРАВЛЕННЫЙ ML Views для обработки видео
"""
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.conf import settings
import os
import sys
import subprocess
import threading
import uuid
from datetime import datetime
import re

from web.database.models import Animal, Video, Analysis, LamenessAnalysis

# ПРОСТАЯ ФУНКЦИЯ ДЛЯ ЗАПУСКА ВАШЕГО ДЕТЕКТОРА
def run_your_detector(video_path, video_id):
    """
    Запускает final_real_detector_correct.py и парсит результаты
    """
    try:
        print(f"\n🚀 ЗАПУСК ВАШЕГО ДЕТЕКТОРА")
        print(f"   Видео: {video_path}")
        print(f"   Video ID: {video_id}")
        
        # Папка для результатов
        output_dir = os.path.join(settings.MEDIA_ROOT, "ml_results", f"vid_{video_id}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Команда для запуска
        detector_script = "/home/ais/shared/horseAI/final_real_detector_correct.py"
        
        cmd = [
            sys.executable,
            detector_script,
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
            timeout=600,  # 10 минут
            cwd="/home/ais/shared/horseAI"
        )
        
        print(f"✅ Детектор завершен. Код: {result.returncode}")
        
        # Парсим результаты
        analysis_result = parse_detector_output(result.stdout, result.stderr, output_dir, video_path)
        analysis_result['returncode'] = result.returncode
        analysis_result['success'] = result.returncode == 0
        
        if result.returncode != 0:
            analysis_result['error'] = f"Детектор вернул код ошибки: {result.returncode}"
            if result.stderr:
                analysis_result['error_detail'] = result.stderr[:500]
        
        return analysis_result
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Таймаут анализа (более 10 минут)',
            'video_path': video_path
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Ошибка запуска детектора: {str(e)}',
            'video_path': video_path
        }

def parse_detector_output(stdout, stderr, output_dir, video_path):
    """
    Парсит вывод вашего детектора и извлекает результаты
    """
    result = {
        'success': True,
        'video_path': video_path,
        'output_dir': output_dir,
        'is_lame': None,
        'lameness_probability': 0.0,
        'confidence': 0.0,
        'diagnosis': 'Не определено',
        'diagnosis_note': '',
        'files': []
    }
    
    # Парсим строки вывода
    lines = stdout.split('\n')
    
    for line in lines:
        line_lower = line.lower()
        
        # Вероятность хромоты
        if 'вероятность хромоты:' in line:
            try:
                # Ищем число с процентами
                match = re.search(r'(\d+\.?\d*)%', line)
                if match:
                    result['lameness_probability'] = float(match.group(1))
            except:
                pass
        
        # Уверенность
        elif 'уверенность:' in line or 'уверенность анализа:' in line:
            try:
                match = re.search(r'(\d+\.?\d*)%', line)
                if match:
                    result['confidence'] = float(match.group(1))
            except:
                pass
        
        # Диагноз
        elif 'диагноз:' in line:
            try:
                parts = line.split('Диагноз:')
                if len(parts) > 1:
                    result['diagnosis'] = parts[1].strip()
            except:
                pass
        
        # Хромая/Здоровая
        elif 'хромая' in line_lower:
            result['is_lame'] = True
        elif 'здоровая' in line_lower and 'вероятно' not in line_lower:
            result['is_lame'] = False
        
        # Примечание
        elif 'примечание:' in line:
            try:
                parts = line.split('Примечание:')
                if len(parts) > 1:
                    result['diagnosis_note'] = parts[1].strip()
            except:
                pass
    
    # Ищем созданные файлы
    video_stem = os.path.splitext(os.path.basename(video_path))[0]
    
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if video_stem in file:
                file_path = os.path.join(root, file)
                file_type = os.path.splitext(file)[1].replace('.', '')
                
                result['files'].append({
                    'name': file,
                    'path': file_path,
                    'type': file_type,
                    'url': file_path.replace(settings.MEDIA_ROOT, settings.MEDIA_URL)
                })
    
    return result

def save_analysis_to_db(video_obj, analysis_result):
    """
    Сохраняет результаты анализа в БД
    """
    try:
        # Создаем запись в Analysis
        analysis = Analysis.objects.create(
            video=video_obj,
            analysis_date=datetime.now(),
            is_lame=analysis_result.get('is_lame'),
            lameness_probability=analysis_result.get('lameness_probability'),
            confidence=analysis_result.get('confidence'),
            diagnosis=analysis_result.get('diagnosis'),
            diagnosis_note=analysis_result.get('diagnosis_note'),
            analysis_status='completed'
        )
        
        # Если есть файлы, сохраняем пути
        if analysis_result.get('files'):
            # Сохраняем путь к файлу результатов если есть .txt
            for file_info in analysis_result['files']:
                if file_info['type'] == 'txt' and 'result' in file_info['name'].lower():
                    analysis.analysis_video_path = file_info['path']
                    break
        
        analysis.save()
        print(f"✅ Анализ сохранен в БД: ID {analysis.analysis_id}")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Ошибка сохранения в БД: {e}")
        return None

# VIEW ФУНКЦИИ
@csrf_exempt
@login_required
def upload_video_for_analysis(request):
    """
    Загружает видео и запускает анализ
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST метод'})
    
    try:
        print(f"\n📥 ЗАГРУЗКА ВИДЕО ДЛЯ АНАЛИЗА")
        
        # Получаем файл
        video_file = request.FILES.get('video_file')
        animal_id = request.POST.get('animal_id')
        
        if not video_file:
            return JsonResponse({'success': False, 'error': 'Выберите видео'})
        
        print(f"📹 Видео: {video_file.name}")
        print(f"🐴 ID животного: {animal_id}")
        
        # Сохраняем видео в медиа папку
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4()[:8]}_{video_file.name}"
        videos_dir = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(videos_dir, exist_ok=True)
        
        video_path = os.path.join(videos_dir, filename)
        
        with open(video_path, 'wb') as f:
            for chunk in video_file.chunks():
                f.write(chunk)
        
        print(f"💾 Видео сохранено: {video_path}")
        
        # Получаем животное
        animal = None
        if animal_id:
            try:
                animal = Animal.objects.get(animal_id=animal_id)
                print(f"🐴 Животное: {animal.name}")
            except Animal.DoesNotExist:
                print(f"⚠️ Животное с ID {animal_id} не найдено")
        
        # Создаем запись Video в БД
        video_obj = Video.objects.create(
            animal=animal if animal else None,
            user=request.user.customuser if hasattr(request.user, 'customuser') else None,
            file_path=video_path,
            upload_date=datetime.now(),
            duration=0,  # можно вычислить позже
            resolution='unknown',
            analysis_status='pending'
        )
        
        print(f"📋 Видео записано в БД: ID {video_obj.video_id}")
        
        # Запускаем анализ в отдельном потоке
        def run_analysis_async():
            print(f"🧪 Запуск анализа видео ID {video_obj.video_id}...")
            
            # Запускаем детектор
            analysis_result = run_your_detector(video_path, video_obj.video_id)
            
            if analysis_result.get('success'):
                print(f"✅ Анализ завершен успешно")
                
                # Сохраняем в БД
                analysis_obj = save_analysis_to_db(video_obj, analysis_result)
                
                if analysis_obj:
                    # Обновляем статус видео
                    video_obj.analysis_status = 'completed'
                    video_obj.save()
                    
                    print(f"🎉 Анализ сохранен. ID анализа: {analysis_obj.analysis_id}")
                else:
                    print(f"⚠️ Анализ не сохранен в БД")
            else:
                print(f"❌ Ошибка анализа: {analysis_result.get('error')}")
                
                # Обновляем статус ошибки
                video_obj.analysis_status = 'failed'
                video_obj.save()
        
        # Запускаем в фоне
        thread = threading.Thread(target=run_analysis_async)
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'success': True,
            'message': 'Видео загружено и анализ запущен',
            'video_id': video_obj.video_id,
            'video_path': video_path,
            'animal_id': animal_id
        })
        
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Ошибка загрузки: {str(e)}'
        }, status=500)

@csrf_exempt
@login_required
def get_analysis_status(request, task_id=None):
    """
    Получает статус анализа
    """
    try:
        # task_id - это video_id
        video_id = task_id or request.GET.get('video_id')
        
        if not video_id:
            return JsonResponse({
                'success': False,
                'error': 'Укажите video_id'
            })
        
        # Ищем видео
        video = Video.objects.get(video_id=video_id)
        
        # Ищем связанный анализ
        analysis = Analysis.objects.filter(video=video).first()
        
        if analysis:
            status_info = {
                'success': True,
                'video_id': video_id,
                'status': 'completed',
                'analysis_id': analysis.analysis_id,
                'is_lame': analysis.is_lame,
                'lameness_probability': analysis.lameness_probability,
                'confidence': analysis.confidence,
                'diagnosis': analysis.diagnosis,
                'diagnosis_note': analysis.diagnosis_note,
                'analysis_date': analysis.analysis_date.strftime('%Y-%m-%d %H:%M:%S') if analysis.analysis_date else None
            }
        else:
            status_info = {
                'success': True,
                'video_id': video_id,
                'status': video.analysis_status or 'processing',
                'analysis_id': None
            }
        
        return JsonResponse(status_info)
        
    except Video.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Видео с ID {video_id} не найдено'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка: {str(e)}'
        })

@csrf_exempt
@login_required
def save_analysis_result(request):
    """
    Сохраняет результаты анализа (вызывается из JS)
    """
    try:
        data = json.loads(request.body)
        
        video_id = data.get('video_id')
        analysis_data = data.get('analysis_data')
        
        if not video_id or not analysis_data:
            return JsonResponse({
                'success': False,
                'error': 'Не указаны video_id или analysis_data'
            })
        
        # Находим видео
        video = Video.objects.get(video_id=video_id)
        
        # Создаем анализ
        analysis = Analysis.objects.create(
            video=video,
            analysis_date=datetime.now(),
            is_lame=analysis_data.get('is_lame'),
            lameness_probability=analysis_data.get('lameness_probability'),
            confidence=analysis_data.get('confidence'),
            diagnosis=analysis_data.get('diagnosis'),
            diagnosis_note=analysis_data.get('diagnosis_note'),
            analysis_status='completed'
        )
        
        # Обновляем статус видео
        video.analysis_status = 'completed'
        video.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Результаты сохранены',
            'analysis_id': analysis.analysis_id
        })
        
    except Video.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Видео с ID {video_id} не найдено'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка сохранения: {str(e)}'
        })

# HTML PAGES
@login_required
def video_upload_page(request):
    """Страница загрузки видео"""
    animals = Animal.objects.filter(user=request.user.customuser)
    return render(request, 'frontend/video_upload.html', {'animals': animals})

@login_required
def analysis_results_page(request):
    """Страница результатов анализов"""
    # Получаем анализы через связанные видео
    user_videos = Video.objects.filter(user=request.user.customuser)
    analyses = Analysis.objects.filter(video__in=user_videos).order_by('-analysis_date')
    
    return render(request, 'frontend/analysis_results.html', {'analyses': analyses})

@login_required
def analysis_detail_page(request, analysis_id):
    """Детальная страница анализа"""
    analysis = get_object_or_404(Analysis, analysis_id=analysis_id)
    return render(request, 'frontend/analysis_detail.html', {'analysis': analysis})

@login_required
def get_video_analysis(request, video_id):
    """Получает анализ по video_id"""
    try:
        video = Video.objects.get(video_id=video_id)
        analysis = Analysis.objects.filter(video=video).first()
        
        if analysis:
            return JsonResponse({
                'success': True,
                'analysis': {
                    'id': analysis.analysis_id,
                    'is_lame': analysis.is_lame,
                    'lameness_probability': analysis.lameness_probability,
                    'confidence': analysis.confidence,
                    'diagnosis': analysis.diagnosis,
                    'diagnosis_note': analysis.diagnosis_note,
                    'date': analysis.analysis_date.strftime('%Y-%m-%d %H:%M:%S') if analysis.analysis_date else None
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Анализ не найден'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_animal_analyses(request, animal_id):
    """Получает все анализы животного"""
    try:
        animal = Animal.objects.get(animal_id=animal_id)
        analyses = Analysis.objects.filter(video__animal=animal).order_by('-analysis_date')
        
        analyses_data = []
        for analysis in analyses:
            analyses_data.append({
                'id': analysis.analysis_id,
                'video_id': analysis.video.video_id if analysis.video else None,
                'is_lame': analysis.is_lame,
                'lameness_probability': analysis.lameness_probability,
                'confidence': analysis.confidence,
                'diagnosis': analysis.diagnosis,
                'diagnosis_note': analysis.diagnosis_note,
                'date': analysis.analysis_date.strftime('%Y-%m-%d %H:%M:%S') if analysis.analysis_date else None
            })
        
        return JsonResponse({
            'success': True,
            'analyses': analyses_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
