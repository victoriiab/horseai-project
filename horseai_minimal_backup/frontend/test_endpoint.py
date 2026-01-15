from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def test_upload_endpoint(request):
    """Тестовый endpoint для проверки работы"""
    print("=== ТЕСТОВЫЙ ENDPOINT ВЫЗВАН ===")
    print(f"Метод: {request.method}")
    print(f"Пользователь: {request.user}")
    
    if request.method == 'POST':
        print(f"Файлы: {list(request.FILES.keys())}")
        print(f"Данные: {dict(request.POST)}")
        
        # Всегда возвращаем успех для теста
        return JsonResponse({
            'success': True,
            'message': 'Тестовый ответ от сервера',
            'video_id': 999,
            'animal_name': 'Тестовое животное',
            'diagnosis': 'Норма (тестовый режим)',
            'lameness_probability': 15.5,
            'is_lame': False,
            'note': 'Это тестовый ответ. Реальная система работает через /api/upload/simple/'
        })
    else:
        return JsonResponse({'success': False, 'error': 'Только POST метод'})
