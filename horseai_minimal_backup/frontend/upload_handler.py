from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from .views import upload_video_simple_api_real
from django.http import JsonResponse

@login_required
@csrf_exempt
def upload_handler_view(request):
    """Обработчик загрузки с перенаправлением"""
    if request.method == 'POST':
        # Вызываем API функцию
        response = upload_video_simple_api_real(request)
        
        # Если это JsonResponse и успех - перенаправляем
        if hasattr(response, 'content'):
            try:
                data = json.loads(response.content)
                if data.get('success'):
                    # Перенаправляем на страницу результатов
                    return redirect('/analysis/results/')
            except:
                pass
        
        # Если что-то пошло не так, возвращаем оригинальный ответ
        return response
    
    return redirect('/video-upload/')
