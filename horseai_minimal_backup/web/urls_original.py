from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.video_upload, name='video_upload'),
    path('animals/', views.animals_list, name='animals_list'),
    path('analysis/', views.analysis_results, name='analysis_results'),
    path('ration/', views.ration_calculation, name='ration_calculation'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('myadmin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('api/stats/', views.get_system_stats, name='get_system_stats'),
    path('api/upload/', views.upload_video_api, name='upload_video_api'),
    path('api/animals/add/', views.add_animal_api, name='add_animal_api'),
    path('api/upload/real/', views.upload_video_api_real, name='upload_video_api_real'),
    path('api/analyze/video/', views.process_video_analysis, name='process_video_analysis'),
    path('api/analysis/status/<int:video_id>/', views.get_analysis_status, name='get_analysis_status'),
]
