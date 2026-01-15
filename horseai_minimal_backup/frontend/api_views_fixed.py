from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

@csrf_exempt
@login_required
def api_upload_video_simple(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST метод'}, status=405)
    
    try:
        print("Получен запрос на загрузку видео")
        
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Требуется аутентификация'
            }, status=401)
        
  
        video_file = request.FILES.get('video_file')
        animal_id = request.POST.get('animal_id', '')
        
        if not video_file:
            return JsonResponse({'success': False, 'error': 'Файл не выбран'})
        
        if not animal_id:
            return JsonResponse({'success': False, 'error': 'Выберите животное'})
        
        print(f"Файл: {video_file.name}, размер: {video_file.size}")
        print(f"ID животного: {animal_id}")
        
        # Импортируем модели
        from web.database.models import Animal, Video, Analysis, User
        from django.utils import timezone
        import os
        import uuid
        
        custom_user = User.objects.get(login=request.user.username)
        
       
        try:
            animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
        except Animal.DoesNotExist:
   
            animal = Animal.objects.create(
                user=custom_user,
                name=f'Лошадь {animal_id}',
                sex='M',
                age=5,
                estimated_weight=500.0,
                created_at=timezone.now()
            )
        
  
        filename = f"{uuid.uuid4().hex[:8]}_{video_file.name}"
        media_dir = '/home/ais/shared/horseAI/media/videos'
        os.makedirs(media_dir, exist_ok=True)
        
        filepath = os.path.join(media_dir, filename)
        
        with open(filepath, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)
        
        video = Video.objects.create(
            animal=animal,
            user=custom_user,
            file_path=f'videos/{filename}',
            upload_date=timezone.now(),
            duration=0.0, 
            resolution='1920x1080',  
            analysis_status='uploaded'
        )
        
     
        analysis = Analysis.objects.create(
            video=video,
            posture='normal',  
            gait_quality='good', 
            size_category='large',  
            estimated_weight=animal.estimated_weight or 500.0,  
            analysis_date=timezone.now(),  
            confidence_score=0.0, 
            diagnosis='Видео загружено, ожидает анализа',
            is_lame=False,
            lameness_probability=0.0,
            lameness_confidence=0.0
        )
        
 
        response_data = {
            'success': True,
            'message': 'Видео успешно загружено!',
            'video_id': video.video_id,
            'analysis_id': analysis.analysis_id,
            'animal_name': animal.name,
            'file_path': video.file_path,
            'analysis_status': 'uploaded'
        }
        
        print(f"Ответ: {response_data}")
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        print(f"Ошибка: {e}")
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()[:500]
        }, status=500)

