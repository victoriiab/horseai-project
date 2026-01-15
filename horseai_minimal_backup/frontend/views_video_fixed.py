from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
from datetime import datetime
from web.database.models import Animal, Video, User
from frontend.forms import VideoUploadForm

@login_required
def video_upload(request):
    """Загрузка видео"""
    try:
        # Получаем кастомного пользователя
        custom_user = User.objects.get(login=request.user.username)
        animals = Animal.objects.filter(user=custom_user)
        
        form = VideoUploadForm(user=request.user)
        
        context = {
            'animals': animals,
            'form': form,
            'page_title': 'Загрузка видео для анализа'
        }
        return render(request, 'frontend/video_upload.html', context)
        
    except Exception as e:
        messages.error(request, f'Ошибка: {e}')
        return render(request, 'frontend/video_upload.html', {'animals': [], 'page_title': 'Загрузка видео'})

@csrf_exempt
@login_required
def upload_video_api(request):
    """API для загрузки видео"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})
    
    try:
        video_file = request.FILES.get('video_file')
        animal_id = request.POST.get('animal_id')
        
        if not video_file:
            return JsonResponse({'success': False, 'error': 'Файл не выбран'})
        
        if not animal_id:
            return JsonResponse({'success': False, 'error': 'Выберите животное'})
        
        # Получаем пользователя и животное
        custom_user = User.objects.get(login=request.user.username)
        animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
        
        # Сохраняем видео
        media_dir = '/home/ais/shared/horseAI/media/videos'
        os.makedirs(media_dir, exist_ok=True)
        
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{video_file.name}"
        filepath = os.path.join(media_dir, filename)
        
        with open(filepath, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)
        
        # Создаем запись в БД
        video = Video.objects.create(
            animal=animal,
            user=custom_user,
            file_path=f'videos/{filename}',
            upload_date=datetime.now(),
            duration=0,
            resolution='unknown',
            analysis_status='uploaded'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Видео успешно загружено',
            'video_id': video.video_id,
            'file_path': video.file_path
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
