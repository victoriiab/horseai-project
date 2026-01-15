from django.urls import path
from . import views
from . import api_views
from . import admin_api

urlpatterns = [
    # Основные страницы
    path('', views.index, name='index'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('animals/', views.animals_list, name='animals'),
    path('ration/', views.ration_calculation, name='ration'),
    path('profile/', views.profile, name='profile'),

    # Загрузка видео и анализ
    path('video-upload/', views.video_upload, name='video_upload'),
    path('analysis/results/', views.analysis_results, name='analysis_results'),

    # SUPER Admin
    path('super-admin/', views.super_admin_panel, name='super_admin'),

    # API endpoints
    path('api/system-stats/', views.get_system_stats, name='system_stats'),

    # ML API
    path('api/ml/analyze/<int:video_id>/', api_views.ml_analyze_video, name='ml_analyze_video'),
    path('api/ml/test/', api_views.ml_test_model, name='ml_test_model'),
    path('api/upload/simple/', api_views.api_upload_video_simple, name='api_upload_simple'),

    # Admin API
    path('api/admin/stats/', admin_api.admin_stats_api, name='admin_stats'),
    path('api/admin/analyses/', admin_api.admin_analyses_api, name='admin_analyses'),
    path('api/admin/analyses/<int:analysis_id>/delete/', admin_api.delete_analysis_api, name='delete_analysis'),
    path('api/admin/analyses/<int:analysis_id>/update/', admin_api.update_analysis_api, name='update_analysis'),

    # API для животных
    path('api/animals/add/', api_views.api_add_animal, name='api_add_animal'),
    path('api/animals/<int:animal_id>/update/', api_views.api_update_animal, name='api_update_animal'),
    path('api/animals/<int:animal_id>/delete/', api_views.api_delete_animal, name='api_delete_animal'),
    path('api/animals/user/', api_views.api_user_animals, name='api_user_animals'),
    path('api/animals/<int:animal_id>/', api_views.api_animal_detail, name='api_animal_detail'),
    path('api/calculate-ration/', api_views.api_calculate_ration, name='api_calculate_ration'),
]
