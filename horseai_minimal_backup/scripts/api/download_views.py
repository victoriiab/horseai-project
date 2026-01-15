from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
import os

from web.database.models import Analysis, Video
from scripts.api.auth_utils import check_user_access

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_analysis_file(request, analysis_id, file_type):
    """
    Скачивание файлов результатов анализа
    
    file_type может быть:
    - 'annotated_video' - размеченное видео
    - 'result_plot' - график анализа
    - 'result_data' - данные H5
    - 'result_json' - JSON данные
    - 'result_report' - текстовый отчет
    - 'original_video' - оригинальное видео
    """
    
    # Получаем анализ
    analysis = get_object_or_404(Analysis, pk=analysis_id)
    
    # Проверяем доступ пользователя
    if not check_user_access(request.user, analysis.video.user.login):
        return Response({'error': 'Нет доступа к этому анализу'}, status=403)
    
    # Определяем путь к файлу в зависимости от типа
    file_path = None
    filename = None
    
    if file_type == 'annotated_video':
        file_path = analysis.annotated_video_path
        if file_path and os.path.exists(file_path):
            filename = f"{analysis.video.animal.name}_размеченное_видео.mp4"
    
    elif file_type == 'result_plot':
        file_path = analysis.result_plot_path
        if file_path and os.path.exists(file_path):
            filename = f"{analysis.video.animal.name}_график_анализа.png"
    
    elif file_type == 'result_data':
        file_path = analysis.result_data_path
        if file_path and os.path.exists(file_path):
            filename = f"{analysis.video.animal.name}_данные_анализа.h5"
    
    elif file_type == 'result_json':
        file_path = analysis.result_json_path
        if file_path and os.path.exists(file_path):
            filename = f"{analysis.video.animal.name}_данные.json"
    
    elif file_type == 'result_report':
        file_path = analysis.result_report_path
        if file_path and os.path.exists(file_path):
            filename = f"{analysis.video.animal.name}_отчет.txt"
    
    elif file_type == 'original_video':
        # Получаем оригинальное видео
        video = analysis.video
        file_path = video.file_path
        if file_path and os.path.exists(file_path):
            filename = f"{video.animal.name}_оригинальное_видео{os.path.splitext(file_path)[1]}"
    
    # Если файл не найден в БД, попробуем найти его в media папке
    if not file_path or not os.path.exists(file_path):
        # Пробуем найти файлы по шаблону
        file_path = find_analysis_file(analysis, file_type)
    
    if not file_path or not os.path.exists(file_path):
        return Response({
            'error': 'Файл не найден',
            'file_type': file_type,
            'analysis_id': analysis_id,
            'suggestion': 'Файл мог быть удален или еще не создан'
        }, status=404)
    
    # Если filename не установлен, берем из пути
    if not filename:
        filename = os.path.basename(file_path)
    
    # Отдаем файл
    try:
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Устанавливаем Content-Type в зависимости от типа файла
        if file_type.endswith('video'):
            response['Content-Type'] = 'video/mp4'
        elif file_type.endswith('plot'):
            response['Content-Type'] = 'image/png'
        elif file_type.endswith('json'):
            response['Content-Type'] = 'application/json'
        elif file_type.endswith('report'):
            response['Content-Type'] = 'text/plain'
        elif file_type.endswith('data'):
            response['Content-Type'] = 'application/octet-stream'
        
        return response
        
    except Exception as e:
        return Response({'error': f'Ошибка чтения файла: {str(e)}'}, status=500)

def find_analysis_file(analysis, file_type):
    """Поиск файла анализа в media папке если путь не сохранен в БД"""
    import glob
    
    media_root = '/home/ais/shared/horseAI/media'
    
    # Ищем по video_id или имени файла
    video_filename = os.path.basename(analysis.video.file_path) if analysis.video.file_path else ""
    base_name = os.path.splitext(video_filename)[0] if video_filename else f"video_{analysis.video_id}"
    
    search_patterns = {
        'annotated_video': [
            f"{media_root}/results/*{base_name}*labeled*.mp4",
            f"{media_root}/ml_results/*{base_name}*labeled*.mp4",
            f"{media_root}/results/*labeled*.mp4",
        ],
        'result_plot': [
            f"{media_root}/results/results/*{base_name}*result.png",
            f"{media_root}/results/*{base_name}*result.png",
            f"{media_root}/results/results/*result.png",
        ],
        'result_data': [
            f"{media_root}/results/*{base_name}*.h5",
            f"{media_root}/results/*.h5",
        ],
        'result_json': [
            f"{media_root}/results/*{base_name}*.json",
            f"{media_root}/results/*.json",
        ],
    }
    
    if file_type in search_patterns:
        for pattern in search_patterns[file_type]:
            files = glob.glob(pattern)
            if files:
                # Берем самый новый файл
                return max(files, key=os.path.getctime)
    
    return None

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_analysis_files_list(request, analysis_id):
    """Получить список доступных файлов для анализа"""
    
    analysis = get_object_or_404(Analysis, pk=analysis_id)
    
    # Проверяем доступ пользователя
    if not check_user_access(request.user, analysis.video.user.login):
        return Response({'error': 'Нет доступа'}, status=403)
    
    files = []
    
    # Проверяем каждый тип файла
    file_types = [
        ('annotated_video', 'Размеченное видео', 'video/mp4'),
        ('result_plot', 'График анализа', 'image/png'),
        ('result_data', 'Данные анализа (H5)', 'application/octet-stream'),
        ('result_json', 'JSON данные', 'application/json'),
        ('original_video', 'Оригинальное видео', 'video/mp4'),
    ]
    
    for file_type, description, content_type in file_types:
        file_path = None
        
        # Сначала проверяем путь в БД
        if file_type == 'annotated_video' and analysis.annotated_video_path:
            file_path = analysis.annotated_video_path
        elif file_type == 'result_plot' and analysis.result_plot_path:
            file_path = analysis.result_plot_path
        elif file_type == 'result_data' and analysis.result_data_path:
            file_path = analysis.result_data_path
        elif file_type == 'result_json' and analysis.result_json_path:
            file_path = analysis.result_json_path
        elif file_type == 'original_video' and analysis.video.file_path:
            file_path = analysis.video.file_path
        
        # Если не найден в БД, ищем в файловой системе
        if not file_path or not os.path.exists(file_path):
            file_path = find_analysis_file(analysis, file_type)
        
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            files.append({
                'type': file_type,
                'description': description,
                'path': file_path,
                'filename': os.path.basename(file_path),
                'size': file_size,
                'size_human': f"{file_size / 1024 / 1024:.2f} MB" if file_size > 0 else "0 MB",
                'url': f"/api/analysis/{analysis_id}/download/{file_type}/",
                'content_type': content_type,
                'exists': True
            })
        else:
            files.append({
                'type': file_type,
                'description': description,
                'exists': False
            })
    
    return Response({
        'analysis_id': analysis_id,
        'animal_name': analysis.video.animal.name,
        'files': files,
        'total_files': len([f for f in files if f['exists']])
    })
