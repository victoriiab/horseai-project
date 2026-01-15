from django.urls import path
from . import views
from . import api_views
from . import real_ml_views_final as ml_views

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

    # API endpoints из api_views.py
    path('api/animals/add/', api_views.api_add_animal, name='api_add_animal'),
    path('api/animals/<int:animal_id>/update/', api_views.api_update_animal, name='api_update_animal'),
    path('api/animals/<int:animal_id>/delete/', api_views.api_delete_animal, name='api_delete_animal'),
    path('api/animals/user/', api_views.api_user_animals, name='api_user_animals'),
    path('api/animals/<int:animal_id>/', api_views.api_animal_detail, name='api_animal_detail'),
    path('api/calculate-ration/', api_views.api_calculate_ration, name='api_calculate_ration'),

    # REAL ML endpoints
    path('api/upload/real-ml-final/', ml_views.upload_video_real_ml_final, name='upload_video_real_ml_final'),
    path('analysis/status/<int:video_id>/', ml_views.analysis_status_final, name='analysis_status_final'),
    path('api/analysis/status/<int:video_id>/', ml_views.get_analysis_status_api_final, name='get_analysis_status_api_final'),
    path('analysis/report/<int:video_id>/download/', ml_views.download_ml_report, name='download_ml_report'),
]

print("✅ URLs загружены (финальная версия с ML)")
