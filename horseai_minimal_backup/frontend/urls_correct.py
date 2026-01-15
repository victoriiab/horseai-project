from django.urls import path
from . import views
from .api_views import (
    api_upload_video_simple, api_user_animals, api_add_animal,
    api_update_animal, api_delete_animal, api_animal_detail,
    api_calculate_ration, api_health_check, ml_analyze_video,
    ml_test_model, api_upload_video_with_ml
)
from .status_views import analysis_status

urlpatterns = [
    # Основные страницы
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Страницы приложения
    path('animals/', views.animals, name='animals'),
    path('video-upload/', views.video_upload, name='video_upload'),
    path('analysis/results/', views.analysis_results, name='analysis_results'),
    path('analysis/<int:analysis_id>/', views.analysis_detail, name='analysis_detail'),
    path('ration/', views.ration_view, name='ration'),
    path('profile/', views.profile_view, name='profile'),
    path('super-admin/', views.super_admin_view, name='super_admin'),
    
    # Страница статуса анализа
    path('analysis/status/', analysis_status, name='analysis_status'),
    
    # API endpoints
    path('api/upload/simple/', api_upload_video_simple, name='api_upload_simple'),
    path('api/upload/real-ml/', api_upload_video_with_ml, name='api_upload_real_ml'),
    path('api/animals/', api_user_animals, name='api_user_animals'),
    path('api/animals/add/', api_add_animal, name='api_add_animal'),
    path('api/animals/<int:animal_id>/', api_animal_detail, name='api_animal_detail'),
    path('api/animals/<int:animal_id>/update/', api_update_animal, name='api_update_animal'),
    path('api/animals/<int:animal_id>/delete/', api_delete_animal, name='api_delete_animal'),
    
    # ML API
    path('api/ml/analyze/<int:video_id>/', ml_analyze_video, name='ml_analyze_video'),
    path('api/ml/test/', ml_test_model, name='ml_test_model'),
    
    # Рационы
    path('api/ration/calculate/', api_calculate_ration, name='api_calculate_ration'),
    
    # Система
    path('api/health/', api_health_check, name='api_health_check'),
]

# Статические страницы для тестирования
urlpatterns += [
    path('test/upload/', views.test_upload_view, name='test_upload'),
    path('test/animals/', views.test_animals_view, name='test_animals'),
]
