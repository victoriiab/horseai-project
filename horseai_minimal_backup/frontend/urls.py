from django.urls import path
from . import views
from . import api_views
from . import status_views

import sys
import os

sys.path.insert(0, '/home/ais/shared/horseAI/scripts')

try:
    from api import super_admin_views
    print("✅ Super admin views импортированы успешно")
    HAS_SUPER_ADMIN_VIEWS = True
except ImportError as e:
    print(f"⚠️ Ошибка импорта super_admin_views: {e}")
    HAS_SUPER_ADMIN_VIEWS = False
    class SuperAdminViewsStub:
        @staticmethod
        def super_admin_stats(request):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_system_health(request):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_users(request):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_user_detail(request, user_id):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_add_user(request):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_edit_user(request, user_id):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_toggle_user_status(request, user_id):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_delete_user(request, user_id):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_animals(request):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_videos(request):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_video_detail(request, video_id):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_delete_video(request, video_id):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_analyses(request):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_analysis_detail(request, analysis_id):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_update_analysis(request, analysis_id):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_delete_analysis(request, analysis_id):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

        @staticmethod
        def super_admin_export_data(request):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Super admin views не загружены'}, status=501)

    super_admin_views = SuperAdminViewsStub()

urlpatterns = [
    # ========== ОСНОВНЫЕ СТРАНИЦЫ ==========
    path('', views.index, name='index'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),

    # ========== ПРИЛОЖЕНИЕ ==========
    path('animals/', views.animals_list, name='animals'),
    path('video-upload/', views.video_upload, name='video_upload'),
    path('video-upload/direct/', views.video_upload_direct, name='video_upload_direct'),
    path('analysis/results/', views.analysis_results, name='analysis_results'),
    path('ration/', views.ration_calculation, name='ration'),
    path('profile/', views.profile, name='profile'),

    # ========== АДМИНКА ==========
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('super-admin/', views.super_admin_panel, name='super_admin'),

    # ========== АНАЛИЗЫ ==========
    path('analysis/<int:analysis_id>/', views.get_analysis_details, name='analysis_detail'),
    path('analysis/status/<int:video_id>/', views.analysis_status_page, name='analysis_status'),

    # ========== API ИЗ VIEWS.PY ==========
    path('api/system-stats/', views.get_system_stats, name='system_stats'),
    path('api/upload/simple-real/', views.upload_video_simple_api_real, name='api_upload_simple_real'),
    path('api/upload/horse-detector/', views.upload_video_horse_detector, name='upload_horse_detector'),
    path('api/upload/with-adapter/', views.upload_video_with_adapter, name='upload_with_adapter'),
    path('api/analysis/status/<int:video_id>/json/', views.get_analysis_status_json, name='analysis_status_json'),

    # API для животных
    path('api/animals/list/', views.api_get_animals, name='api_get_animals'),
    path('api/animals/add/', views.api_add_animal, name='api_add_animal'),
    path('api/animals/<int:animal_id>/', views.api_get_animal_detail, name='api_animal_detail'),
    path('api/animals/<int:animal_id>/update/', views.api_update_animal, name='api_update_animal'),
    path('api/animals/<int:animal_id>/delete/', views.api_delete_animal, name='api_delete_animal'),

    path('api/analysis/<int:analysis_id>/detail/', views.api_get_analysis_detail, name='api_analysis_detail'),
    path('api/analysis/<int:analysis_id>/delete/', views.api_delete_analysis, name='api_delete_analysis'),
    path('api/video-proxy/', views.api_video_proxy, name='api_video_proxy'),
    path('api/analysis/<int:analysis_id>/find-files/', views.api_find_analysis_files, name='api_find_analysis_files'),
    path('analysis/<int:analysis_id>/update-confidence/', views.update_analysis_confidence, name='update_analysis_confidence'),
    path('ration/history/', views.ration_history, name='ration_history'),
    path('ration/<int:ration_id>/', views.ration_detail, name='ration_detail'),

]

if HAS_SUPER_ADMIN_VIEWS:
    urlpatterns += [
        # ========== СТАТИСТИКА ==========
        path('super-admin/stats/', super_admin_views.super_admin_stats, name='super_admin_stats'),
        path('super-admin/system-health/', super_admin_views.super_admin_system_health, name='super_admin_system_health'),

        # ========== ПОЛЬЗОВАТЕЛИ ==========
        path('super-admin/users/', super_admin_views.super_admin_users, name='super_admin_users'),
        path('super-admin/users/<int:user_id>/', super_admin_views.super_admin_user_detail, name='super_admin_user_detail'),
        path('super-admin/users/add/', super_admin_views.super_admin_add_user, name='super_admin_add_user'),
        path('super-admin/users/<int:user_id>/edit/', super_admin_views.super_admin_edit_user, name='super_admin_edit_user'),
        path('super-admin/users/<int:user_id>/toggle-status/', super_admin_views.super_admin_toggle_user_status, name='super_admin_toggle_user_status'),
        path('super-admin/users/<int:user_id>/delete/', super_admin_views.super_admin_delete_user, name='super_admin_delete_user'),

        # ========== ЖИВОТНЫЕ ==========
        path('super-admin/animals/', super_admin_views.super_admin_animals, name='super_admin_animals'),

        # ========== ВИДЕО ==========
        path('super-admin/videos/', super_admin_views.super_admin_videos, name='super_admin_videos'),
        path('super-admin/videos/<int:video_id>/', super_admin_views.super_admin_video_detail, name='super_admin_video_detail'),
        path('super-admin/videos/<int:video_id>/delete/', super_admin_views.super_admin_delete_video, name='super_admin_delete_video'),

        # ========== АНАЛИЗЫ ==========
        path('super-admin/analyses/', super_admin_views.super_admin_analyses, name='super_admin_analyses'),
        path('super-admin/analyses/<int:analysis_id>/', super_admin_views.super_admin_analysis_detail, name='super_admin_analysis_detail'),
        path('super-admin/analyses/<int:analysis_id>/update/', super_admin_views.super_admin_update_analysis, name='super_admin_update_analysis'),
        path('super-admin/analyses/<int:analysis_id>/delete/', super_admin_views.super_admin_delete_analysis, name='super_admin_delete_analysis'),

        # ========== ЭКСПОРТ ==========
        path('super-admin/export/', super_admin_views.super_admin_export_data, name='super_admin_export_data'),
        # ========== РАЦИОНЫ ==========
        path('super-admin/rations/', super_admin_views.super_admin_rations, name='super_admin_rations'),
        path('super-admin/rations/<int:ration_id>/', super_admin_views.super_admin_ration_detail, name='super_admin_ration_detail'),
        path('super-admin/rations/<int:ration_id>/delete/', super_admin_views.super_admin_delete_ration, name='super_admin_delete_ration'),
                # ========== ЖИВОТНЫЕ ==========
        path('super-admin/animals/', super_admin_views.super_admin_animals, name='super_admin_animals'),
        path('super-admin/animals/<int:animal_id>/', super_admin_views.super_admin_animal_detail, name='super_admin_animal_detail'),
        path('super-admin/animals/<int:animal_id>/edit/', super_admin_views.super_admin_edit_animal, name='super_admin_edit_animal'),
        path('super-admin/animals/<int:animal_id>/delete/', super_admin_views.super_admin_delete_animal, name='super_admin_delete_animal'),
        path('super-admin/animals/add/', views.add_animal, name='super_admin_add_animal'),
    ]


try:
    if hasattr(api_views, 'api_upload_video_simple'):
        urlpatterns.append(path('api/upload/simple/', api_views.api_upload_video_simple, name='api_upload_simple'))
except:
    pass

try:
    if hasattr(api_views, 'api_upload_video_with_ml'):
        urlpatterns.append(path('api/upload/real-ml/', api_views.api_upload_video_with_ml, name='api_upload_real_ml'))
except:
    pass

try:
    if hasattr(api_views, 'api_user_animals'):
        urlpatterns.append(path('api/animals/', api_views.api_user_animals, name='api_user_animals'))
except:
    pass

try:
    if hasattr(api_views, 'api_health_check'):
        urlpatterns.append(path('api/health/', api_views.api_health_check, name='api_health_check'))
except:
    pass

try:
    if hasattr(api_views, 'ml_analyze_video'):
        urlpatterns.append(path('api/ml/analyze/<int:video_id>/', api_views.ml_analyze_video, name='ml_analyze_video'))
except:
    pass

try:
    if hasattr(api_views, 'ml_test_model'):
        urlpatterns.append(path('api/ml/test/', api_views.ml_test_model, name='ml_test_model'))
except:
    pass

try:
    if hasattr(api_views, 'api_calculate_ration'):
        urlpatterns.append(path('api/ration/calculate/', api_views.api_calculate_ration, name='api_calculate_ration'))
except:
    pass

try:
    if hasattr(status_views, 'analysis_status'):
        urlpatterns.append(path('analysis/status/page/', status_views.analysis_status, name='analysis_status_page'))
except:
    pass
