from django.urls import path
from .upload_lameness import (
    upload_lameness_page,
    upload_lameness_video,
    get_lameness_status,
    download_annotated_video,
    get_analysis_logs,
    get_lameness_graphs,
    generate_report,
    test_page
)

urlpatterns = [
    path('upload-lameness/', upload_lameness_page, name='upload_lameness'),
    path('api/lameness/upload/', upload_lameness_video, name='upload_lameness_video'),
    path('api/lameness/status/<str:video_id>/', get_lameness_status, name='get_lameness_status'),
    path('api/lameness/download/<str:video_id>/', download_annotated_video, name='download_lameness_video'),
    path('api/lameness/logs/<str:video_id>/', get_analysis_logs, name='get_analysis_logs'),
    path('api/lameness/graphs/<str:video_id>/', get_lameness_graphs, name='get_lameness_graphs'),
    path('api/lameness/report/<str:video_id>/', generate_report, name='generate_report'),
    path('test/', test_page, name='test_page'),
]
