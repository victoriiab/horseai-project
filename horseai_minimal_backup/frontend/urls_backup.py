from django.urls import path
from . import ml_views
from . import views
from . import api_views
from . import status_views

urlpatterns = [
    # Основные страницы
    path('', views.index, name='index'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),

    # Страницы приложения
    path('animals/', views.animals_list, name='animals'),
    path('video-upload/', views.video_upload, name='video_upload'),
    path('analysis/results/', views.analysis_results, name='analysis_results'),
    path('analysis/<int:analysis_id>/', views.get_analysis_details, name='analysis_detail'),
    path('ration/', views.ration_calculation, name='ration'),
    path('profile/', views.profile, name='profile'),
    path('super-admin/', views.super_admin_panel, name='super_admin'),

    # Страница статуса анализа
    path('analysis/status/', status_views.analysis_status, name='analysis_status'),

    # API endpoints
    path('api/upload/simple/', api_views.api_upload_video_simple, name='api_upload_simple'),
    path('api/upload/real-ml/', api_views.api_upload_video_with_ml, name='api_upload_real_ml'),
    path('api/animals/', api_views.api_user_animals, name='api_user_animals'),
    path('api/animals/add/', api_views.api_add_animal, name='api_add_animal'),
    path('api/animals/<int:animal_id>/', api_views.api_animal_detail, name='api_animal_detail'),
    path('api/animals/<int:animal_id>/update/', api_views.api_update_animal, name='api_update_animal'),
    path('api/animals/<int:animal_id>/delete/', api_views.api_delete_animal, name='api_delete_animal'),

    # ML API
    path('api/ml/analyze/<int:video_id>/', api_views.ml_analyze_video, name='ml_analyze_video'),
    path('api/ml/test/', api_views.ml_test_model, name='ml_test_model'),

    # Рационы
    path('api/ration/calculate/', api_views.api_calculate_ration, name='api_calculate_ration'),

    # Система
    path('api/health/', api_views.api_health_check, name='api_health_check'),
    
    # Дополнительные API из views.py
    path('api/upload/horse-detector/', views.upload_video_horse_detector, name='upload_horse_detector'),
    path('api/upload/with-adapter/', views.upload_video_with_adapter, name='upload_with_adapter'),
    path('api/analysis/status/<int:video_id>/', views.get_analysis_status_json, name='analysis_status_json'),
    path('api/system-stats/', views.get_system_stats, name='system_stats'),
]

# Статические страницы для тестирования
urlpatterns += [
    path('test/upload/', views.test_upload_page, name='test_upload'),
    path('test/animals/', views.animals_list, name='test_animals'),
]

# Импортируем новые views
from .video_views import (
    api_upload_video, api_video_status, 
    analysis_status_page, api_queue_stats
)

# Добавляем новые URL patterns
urlpatterns += [
    # Рабочий API загрузки видео
    path('api/video/upload/', api_upload_video, name='api_video_upload'),
    path('api/video/status/<int:video_id>/', api_video_status, name='api_video_status'),
    path('analysis/status/<int:video_id>/', analysis_status_page, name='analysis_status_page'),
    
    # Статистика очереди (для админов)
    path('api/queue/stats/', api_queue_stats, name='api_queue_stats'),
    
    # Удаляем старые нерабочие URL (закоментируем на всякий случай)
    # path('api/upload/simple/', api_views.api_upload_video_simple, name='api_upload_simple'),
    # path('api/upload/real-ml/', api_views.api_upload_video_with_ml, name='api_upload_real_ml'),
]

# ML анализ видео
path('api/ml/upload/', ml_views.upload_video_for_analysis, name='ml_upload_video'),
path('api/ml/status/<str:task_id>/', ml_views.get_analysis_status, name='ml_analysis_status'),
path('api/ml/save-result/', ml_views.save_analysis_result, name='ml_save_result'),
path('api/ml/video/<int:video_id>/analysis/', ml_views.get_video_analysis, name='ml_get_video_analysis'),
path('api/ml/animal/<int:animal_id>/analyses/', ml_views.get_animal_analyses, name='ml_get_animal_analyses'),
