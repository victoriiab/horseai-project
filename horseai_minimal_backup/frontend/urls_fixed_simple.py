from django.urls import path
from . import views
from . import api_views
from django.shortcuts import render

urlpatterns = [
    # Основные страницы
    path('', views.index, name='index'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('animals/', views.animals_list, name='animals'),
    path('ration/', views.ration_calculation, name='ration'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.admin_dashboard, name='dashboard'),

    # Загрузка видео и анализ
    path('video-upload/', views.video_upload, name='video_upload'),
    path('analysis/results/', views.analysis_results, name='analysis_results'),

    # API endpoints из views.py
    path('api/system-stats/', views.get_system_stats, name='system_stats'),
    path('api/upload/real/', views.upload_video_api_real, name='upload_video_real'),
    path('api/upload/simple/', views.upload_video_simple_api_real, name='upload_video_simple'),

    # API endpoints из api_views.py (НЕ ТРОГАТЬ!)
    path('api/animals/add/', api_views.api_add_animal, name='api_add_animal'),
    path('api/animals/<int:animal_id>/update/', api_views.api_update_animal, name='api_update_animal'),
    path('api/animals/<int:animal_id>/delete/', api_views.api_delete_animal, name='api_delete_animal'),
    path('api/animals/user/', api_views.api_user_animals, name='api_user_animals'),
    path('api/animals/<int:animal_id>/', api_views.api_animal_detail, name='api_animal_detail'),
    path('api/calculate-ration/', api_views.api_calculate_ration, name='api_calculate_ration'),
    path('api/analyze-video/<int:video_id>/', api_views.api_analyze_video, name='api_analyze_video'),

    # Тестовые страницы (опционально)
    path('simple-test/', lambda request: render(request, 'frontend/simple_test.html'), name='simple_test'),
]
