"""
Исправленный API для детальной страницы анализа
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
import os
import glob
import json

try:
    from web.database.models import Analysis, Video, Animal, User
    from .serializers import AnalysisSerializer
    HAS_MODELS = True
except ImportError:
    HAS_MODELS = False
    print("⚠️ Модели не импортированы в analysis_views.py")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analysis_detail(request, analysis_id):
    """Детальная информация об анализе"""
    if not HAS_MODELS:
        return Response({
            'success': False,
            'error': 'Модели не доступны'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        # Находим кастомного пользователя
        custom_user = User.objects.get(login=request.user.username)
        
        # Получаем анализ
        analysis = get_object_or_404(Analysis, analysis_id=analysis_id)
        
        # Проверяем, что анализ принадлежит пользователю
        video = analysis.video
        if not video or video.user != custom_user:
            return Response({
                'success': False,
                'error': 'Доступ запрещен'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Получаем связанные данные
        animal = video.animal
        
        # Получаем имя файла видео
        video_filename = ''
        video_path = ''
        if video.file_path:
            video_filename = os.path.basename(video.file_path)
            video_path = f'/media/{video.file_path}'
        
        # Ищем файлы результатов
        media_root = getattr(settings, 'MEDIA_ROOT', '/home/ais/shared/horseAI/media')
        results_dir = os.path.join(media_root, 'results')
        
        # Базовое имя для поиска (без расширения)
        base_name = os.path.splitext(video_filename)[0] if video_filename else f'analysis_{analysis_id}'
        
        # Ищем все файлы с этим именем
        annotated_video_path = None
        text_report_path = None
        graphic_report_path = None
        pose_data_path = None
        
        if os.path.exists(results_dir):
            # Ищем файлы по шаблону
            for filepath in glob.glob(os.path.join(results_dir, f'*{base_name}*')):
                filename = os.path.basename(filepath)
                rel_path = f'/media/results/{filename}'
                
                if '_labeled' in filename or '_annotated' in filename or 'labeled' in filename.lower():
                    annotated_video_path = rel_path
                elif filename.endswith('.txt') and ('result' in filename.lower() or 'report' in filename.lower()):
                    text_report_path = rel_path
                elif filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg'):
                    graphic_report_path = rel_path
                elif filename.endswith('.h5'):
                    pose_data_path = rel_path
        
        # Если в самом анализе есть путь
        if analysis.analysis_video_path:
            annotated_video_path = analysis.analysis_video_path
        
        # Формируем диагностическое сообщение
        diagnosis = analysis.diagnosis or 'Диагноз не указан'
        if analysis.is_lame:
            diagnosis = f'Вероятность хромоты: {analysis.lameness_probability or 0}% - ' + diagnosis
        
        # Формируем ответ
        response_data = {
            'success': True,
            'analysis': {
                'analysis_id': analysis.analysis_id,
                'animal_name': animal.name if animal else 'Неизвестно',
                'animal_id': animal.animal_id if animal else None,
                'video_filename': video_filename,
                'video_path': video_path,
                'annotated_video_path': annotated_video_path,
                'text_report_path': text_report_path,
                'graphic_report_path': graphic_report_path,
                'pose_data_path': pose_data_path,
                'user_name': custom_user.full_name,
                'created_at': analysis.analysis_date.isoformat() if analysis.analysis_date else None,
                'is_lame': bool(analysis.is_lame),
                'lameness_probability': float(analysis.lameness_probability) if analysis.lameness_probability else 0.0,
                'lameness_confidence': float(analysis.lameness_confidence) if analysis.lameness_confidence else 0.0,
                'confidence_score': float(analysis.confidence_score) if analysis.confidence_score else 0.0,
                'diagnosis': diagnosis,
                'diagnosis_note': analysis.diagnosis_note,
                'posture': analysis.posture,
                'gait_quality': analysis.gait_quality,
            }
        }
        
        return Response(response_data)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Пользователь не найден'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Ошибка сервера: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def analysis_delete(request, analysis_id):
    """Удаление анализа"""
    if not HAS_MODELS:
        return Response({
            'success': False,
            'error': 'Модели не доступны'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        # Находим кастомного пользователя
        custom_user = User.objects.get(login=request.user.username)
        
        # Получаем анализ
        analysis = get_object_or_404(Analysis, analysis_id=analysis_id)
        
        # Проверяем, что анализ принадлежит пользователю
        video = analysis.video
        if not video or video.user != custom_user:
            return Response({
                'success': False,
                'error': 'Доступ запрещен'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Удаляем запись из БД
        analysis.delete()
        
        return Response({
            'success': True,
            'message': 'Анализ удален',
            'deleted_id': analysis_id
        })
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Пользователь не найден'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
