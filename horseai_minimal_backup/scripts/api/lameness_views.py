"""
Views для анализа хромоты
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
import os
import json
from datetime import datetime

from web.database.models import Video, Analysis, Animal, User
from .serializers import AnalysisSerializer
from ..ml_processor import analyze_video_file

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_video_analysis(request, video_id):
    """Запуск анализа видео"""
    try:
        # Получаем видео
        custom_user = User.objects.get(login=request.user.username)
        video = get_object_or_404(Video, video_id=video_id, user=custom_user)
        
        # Проверяем путь к файлу
        video_path = os.path.join('/home/ais/shared/horseAI/media/', video.file_path)
        
        if not os.path.exists(video_path):
            return Response({
                'status': 'error',
                'message': 'Видеофайл не найден на сервере'
            }, status=404)
        
        # Меняем статус
        video.analysis_status = 'processing'
        video.save()
        
        # Запускаем анализ
        analysis_result = analyze_video_file(video_path, video.animal.animal_id)
        
        if not analysis_result.get('success', False):
            video.analysis_status = 'failed'
            video.save()
            
            return Response({
                'status': 'error',
                'message': analysis_result.get('error', 'Неизвестная ошибка анализа')
            }, status=500)
        
        # Создаем запись анализа
        analysis_data = analysis_result['analysis']
        video_info = analysis_result['video_info']
        
        analysis = Analysis.objects.create(
            video=video,
            analysis_date=timezone.now(),
            is_lame=analysis_data['is_lame'],
            lameness_probability=analysis_data['lameness_probability'],
            lameness_confidence=analysis_data['confidence'],
            diagnosis=analysis_data['diagnosis'],
            diagnosis_note=analysis_data['diagnosis_note'],
            gait_quality=analysis_data.get('gait_quality', ''),
            estimated_weight=video.animal.estimated_weight,
            confidence_score=analysis_data['confidence']
        )
        
        # Обновляем статус видео
        video.analysis_status = 'completed'
        video.duration = video_info.get('duration', 0)
        video.resolution = video_info.get('resolution', 'unknown')
        video.save()
        
        serializer = AnalysisSerializer(analysis)
        
        return Response({
            'status': 'success',
            'message': 'Анализ завершен успешно',
            'analysis': serializer.data,
            'video_info': video_info,
            'recommendations': analysis_data.get('recommendations', [])
        })
        
    except Exception as e:
        # В случае ошибки обновляем статус
        try:
            video = Video.objects.get(video_id=video_id)
            video.analysis_status = 'failed'
            video.save()
        except:
            pass
        
        return Response({
            'status': 'error',
            'message': f'Ошибка при анализе: {str(e)}'
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_analysis_status(request, video_id):
    """Получение статуса анализа"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        video = get_object_or_404(Video, video_id=video_id, user=custom_user)
        
        # Получаем последний анализ для этого видео
        analysis = Analysis.objects.filter(video=video).order_by('-analysis_date').first()
        
        data = {
            'video_id': video.video_id,
            'status': video.analysis_status,
            'upload_date': video.upload_date,
            'file_path': video.file_path
        }
        
        if analysis:
            data['analysis'] = {
                'id': analysis.analysis_id,
                'date': analysis.analysis_date,
                'is_lame': analysis.is_lame,
                'lameness_probability': analysis.lameness_probability,
                'diagnosis': analysis.diagnosis,
                'confidence': analysis.lameness_confidence
            }
        
        return Response(data)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_analyses(request):
    """Получение всех анализов пользователя"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        
        # Получаем видео пользователя
        videos = Video.objects.filter(user=custom_user)
        
        # Получаем анализы для этих видео
        analyses = Analysis.objects.filter(video__in=videos).select_related(
            'video', 'video__animal'
        ).order_by('-analysis_date')
        
        result = []
        for analysis in analyses:
            result.append({
                'analysis_id': analysis.analysis_id,
                'animal_name': analysis.video.animal.name,
                'video_id': analysis.video.video_id,
                'analysis_date': analysis.analysis_date,
                'is_lame': analysis.is_lame,
                'lameness_probability': analysis.lameness_probability,
                'diagnosis': analysis.diagnosis,
                'confidence': analysis.lameness_confidence,
                'video_status': analysis.video.analysis_status
            })
        
        return Response({
            'status': 'success',
            'count': len(result),
            'analyses': result
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_analyze_videos(request):
    """Массовый анализ нескольких видео"""
    try:
        video_ids = request.data.get('video_ids', [])
        
        if not video_ids:
            return Response({
                'status': 'error',
                'message': 'Не указаны ID видео для анализа'
            }, status=400)
        
        results = []
        custom_user = User.objects.get(login=request.user.username)
        
        for video_id in video_ids:
            try:
                video = Video.objects.get(video_id=video_id, user=custom_user)
                
                # Проверяем, не анализировалось ли уже
                if video.analysis_status in ['completed', 'processing']:
                    results.append({
                        'video_id': video_id,
                        'status': 'skipped',
                        'message': f'Видео уже в статусе {video.analysis_status}'
                    })
                    continue
                
                # Запускаем анализ
                video_path = os.path.join('/home/ais/shared/horseAI/media/', video.file_path)
                
                if not os.path.exists(video_path):
                    results.append({
                        'video_id': video_id,
                        'status': 'error',
                        'message': 'Файл не найден'
                    })
                    continue
                
                video.analysis_status = 'processing'
                video.save()
                
                analysis_result = analyze_video_file(video_path, video.animal.animal_id)
                
                if analysis_result['success']:
                    analysis_data = analysis_result['analysis']
                    
                    analysis = Analysis.objects.create(
                        video=video,
                        analysis_date=timezone.now(),
                        is_lame=analysis_data['is_lame'],
                        lameness_probability=analysis_data['lameness_probability'],
                        lameness_confidence=analysis_data['confidence'],
                        diagnosis=analysis_data['diagnosis'],
                        diagnosis_note=analysis_data['diagnosis_note']
                    )
                    
                    video.analysis_status = 'completed'
                    video.save()
                    
                    results.append({
                        'video_id': video_id,
                        'status': 'completed',
                        'analysis_id': analysis.analysis_id
                    })
                else:
                    video.analysis_status = 'failed'
                    video.save()
                    
                    results.append({
                        'video_id': video_id,
                        'status': 'error',
                        'message': analysis_result.get('error', 'Неизвестная ошибка')
                    })
                    
            except Exception as e:
                results.append({
                    'video_id': video_id,
                    'status': 'error',
                    'message': str(e)
                })
        
        return Response({
            'status': 'success',
            'total': len(video_ids),
            'results': results
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)
