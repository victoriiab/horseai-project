from django.urls import path
from rest_framework.routers import DefaultRouter

# Импортируем ИСПРАВЛЕННЫЕ простые API функции
from .api_animals_simple_fixed import (
    simple_animal_list, simple_animal_create, simple_animal_detail,
    simple_animal_update, simple_animal_delete, animal_stats
)

urlpatterns = [
    # Исправленные API endpoints (гарантированно работающие)
    path('simple-v2/animals/', simple_animal_list, name='simple_v2_animal_list'),
    path('simple-v2/animals/add/', simple_animal_create, name='simple_v2_animal_create'),
    path('simple-v2/animals/<int:animal_id>/', simple_animal_detail, name='simple_v2_animal_detail'),
    path('simple-v2/animals/<int:animal_id>/update/', simple_animal_update, name='simple_v2_animal_update'),
    path('simple-v2/animals/<int:animal_id>/delete/', simple_animal_delete, name='simple_v2_animal_delete'),
    path('simple-v2/animals/<int:animal_id>/stats/', animal_stats, name='simple_v2_animal_stats'),
]

# Добавим проверочный endpoint для тестирования
from .api_animals_simple_fixed import HAS_MODELS

def check_api_status(request):
    return JsonResponse({
        'status': 'ok',
        'models_available': HAS_MODELS,
        'endpoints': [
            '/api/simple-v2/animals/',
            '/api/simple-v2/animals/add/',
            '/api/simple-v2/animals/<id>/',
            '/api/simple-v2/animals/<id>/update/',
            '/api/simple-v2/animals/<id>/delete/',
        ]
    })

urlpatterns.append(path('simple-v2/status/', check_api_status, name='api_simple_v2_status'))
