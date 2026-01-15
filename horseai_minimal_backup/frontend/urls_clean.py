from django.urls import path
from . import views

urlpatterns = [
    # Основные страницы
    path('', views.index, name='index'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('animals/', views.animals_list, name='animals'),
    path('ration/', views.ration_calculation, name='ration'),

    # Загрузка видео и анализ
    path('video-upload/', views.video_upload, name='video_upload'),
    path('analysis/results/', views.analysis_results, name='analysis_results'),
    path('video-upload/ml/', views.upload_video_real_analysis, name='video_upload_ml'),

    # API endpoints
    path('api/upload/', views.upload_video_api, name='upload_video_api'),
    path('api/upload/real/', views.upload_video_api_real, name='upload_video_api_real'),
    path('api/analysis/status/<int:video_id>/', views.get_analysis_status, name='get_analysis_status'),
    path('api/simple-analysis/', views.create_simple_analysis, name='create_simple_analysis'),
    path('api/system-stats/', views.get_system_stats, name='get_system_stats'),

    # API для животных
    path('api/animals/add/', views.add_animal_api, name='add_animal_api'),
    path('api/animals/<int:animal_id>/', views.get_animal_api, name='get_animal_api'),
    path('api/animals/<int:animal_id>/update/', views.update_animal_api, name='update_animal_api'),
    path('api/animals/<int:animal_id>/delete/', views.delete_animal_api, name='delete_animal_api'),
]
