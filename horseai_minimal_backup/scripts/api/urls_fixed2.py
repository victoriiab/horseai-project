from django.urls import path
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter

# Импортируем ИСПРАВЛЕННЫЕ простые API функции
try:
    from .api_animals_simple_fixed import (
        simple_animal_list, simple_animal_create, simple_animal_detail,
        simple_animal_update, simple_animal_delete, animal_stats
    )
    HAS_API_FUNCTIONS = True
except ImportError as e:
    print(f"⚠️ Ошибка импорта API функций: {e}")
    HAS_API_FUNCTIONS = False

urlpatterns = []

if HAS_API_FUNCTIONS:
    # Исправленные API endpoints (гарантированно работающие)
    urlpatterns += [
        path('simple-v2/animals/', simple_animal_list, name='simple_v2_animal_list'),
        path('simple-v2/animals/add/', simple_animal_create, name='simple_v2_animal_create'),
        path('simple-v2/animals/<int:animal_id>/', simple_animal_detail, name='simple_v2_animal_detail'),
        path('simple-v2/animals/<int:animal_id>/update/', simple_animal_update, name='simple_v2_animal_update'),
        path('simple-v2/animals/<int:animal_id>/delete/', simple_animal_delete, name='simple_v2_animal_delete'),
        path('simple-v2/animals/<int:animal_id>/stats/', animal_stats, name='simple_v2_animal_stats'),
    ]

# Добавим проверочный endpoint для тестирования
def check_api_status(request):
    return JsonResponse({
        'status': 'ok',
        'api_available': HAS_API_FUNCTIONS,
        'endpoints': [
            {'path': '/api/simple-v2/animals/', 'method': 'GET'},
            {'path': '/api/simple-v2/animals/add/', 'method': 'POST'},
            {'path': '/api/simple-v2/animals/<id>/', 'method': 'GET'},
            {'path': '/api/simple-v2/animals/<id>/update/', 'method': 'POST'},
            {'path': '/api/simple-v2/animals/<id>/delete/', 'method': 'DELETE'},
        ]
    })

urlpatterns.append(path('simple-v2/status/', check_api_status, name='api_simple_v2_status'))

# Добавим простой fallback API если основные не работают
def simple_api_fallback(request):
    return JsonResponse({
        'status': 'fallback',
        'message': 'Используется fallback API',
        'endpoints': ['/api/simple-v2/status/']
    })

urlpatterns.append(path('', simple_api_fallback, name='api_root'))
