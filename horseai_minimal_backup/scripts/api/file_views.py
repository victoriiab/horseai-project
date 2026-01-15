import os
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required

@login_required
def check_file_exists(request):
    """Проверка существования файла"""
    path = request.GET.get('path', '')
    
    if not path:
        return JsonResponse({'exists': False, 'error': 'No path provided'})
    
    try:
        # Преобразуем относительный путь в абсолютный
        if path.startswith('/media/'):
            absolute_path = os.path.join(settings.BASE_DIR, path[1:])  # убираем первый /
        else:
            absolute_path = os.path.join(settings.MEDIA_ROOT, path)
        
        # Проверяем существование файла
        exists = os.path.exists(absolute_path)
        
        if exists:
            # Возвращаем URL для доступа к файлу
            if path.startswith('/media/'):
                url = path
            else:
                url = f'/media/{path}'
            
            return JsonResponse({
                'exists': True,
                'url': url,
                'path': absolute_path
            })
        else:
            return JsonResponse({'exists': False, 'path': absolute_path})
            
    except Exception as e:
        return JsonResponse({'exists': False, 'error': str(e)})
