    print(f'DEBUG: Метод: {request.method}')
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

# Импортируем функции для lameness-test из web приложения
try:
    from web.lameness_views import lameness_test, lameness_test_page
    from web.your_real_detector_fixed import upload_video_fixed, get_status_fixed, download_annotated_video_fixed
    from web.simple_api import upload_video_direct, get_status_direct, download_annotated_direct
    from web.final_detector_api import upload_video_final, get_status_final, download_annotated_final
    from web.real_final_api import upload_video_real_final, get_status_real_final, download_annotated_real_final
    has_web_app = True
except ImportError:
    has_web_app = False
    print("Приложение web не найдено, некоторые функции будут недоступны")

# Импортируем views из frontend приложения
from frontend import views as frontend_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Основные страницы frontend
    path('', frontend_views.index, name='index'),
    path('login/', frontend_views.custom_login, name='login'),
    path('dashboard/', frontend_views.admin_dashboard, name='admin_dashboard'),
    path('animals/', frontend_views.animals_list, name='animals'),
    path('ration/', frontend_views.ration_calculation, name='ration'),
    path('video-upload/', frontend_views.video_upload, name='video_upload'),
    path('analysis/results/', frontend_views.analysis_results, name='analysis_results'),
    path('video-upload/ml/', frontend_views.upload_video_real_analysis, name='video_upload_ml'),
    
    # API endpoints frontend
    path('api/upload/', frontend_views.upload_video_api, name='upload_video_api'),
    path('api/upload/real/', frontend_views.upload_video_api_real, name='upload_video_api_real'),
    path('api/analysis/status/<str:video_id>/', frontend_views.get_analysis_status, name='get_analysis_status'),
    path('api/simple-analysis/', frontend_views.create_simple_analysis, name='create_simple_analysis'),
    path('api/system-stats/', frontend_views.get_system_stats, name='get_system_stats'),
    path('api/animals/add/', frontend_views.add_animal_api, name='add_animal_api'),
    
    # Health check
    path('health/', lambda r: JsonResponse({'status': 'healthy'}), name='health'),
]

# Добавляем web приложение если оно доступно
if has_web_app:
    urlpatterns += [
        path('lameness-test/', lameness_test_page, name='lameness_test_page'),
        path('api/lameness/test/', lameness_test, name='lameness_test'),
        path('api/lameness/your/upload/', upload_video_fixed, name='lameness_upload_your'),
        path('api/lameness/your/status/<str:video_id>/', get_status_fixed, name='lameness_status_your'),
        path('api/lameness/your/download/<str:video_id>/', download_annotated_video_fixed, name='lameness_download_your'),
        path('api/lameness/direct/upload/', upload_video_direct, name='lameness_upload_direct'),
        path('api/lameness/direct/status/<str:video_id>/', get_status_direct, name='lameness_status_direct'),
        path('api/lameness/direct/download/<str:video_id>/', download_annotated_direct, name='lameness_download_direct'),
        path('api/lameness/final/upload/', upload_video_final, name='lameness_upload_final'),
        path('api/lameness/final/status/<str:video_id>/', get_status_final, name='lameness_status_final'),
        path('api/lameness/final/download/<str:video_id>/', download_annotated_final, name='lameness_download_final'),
        path('api/lameness/real/upload/', upload_video_real_final, name='lameness_upload_real'),
        path('api/lameness/real/status/<str:video_id>/', get_status_real_final, name='lameness_status_real'),
        path('api/lameness/real/download/<str:video_id>/', download_annotated_real_final, name='lameness_download_real'),
    ]

# Статические файлы в development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
path('api/test/', test_api, name='test_api'),
