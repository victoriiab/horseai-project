import threading
import json
from pathlib import Path
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from web.database.models import Video, Analysis
from core.detector.horse_lameness_detector import HorseLamenessDetector

class LamenessAnalysisViewSet(viewsets.ViewSet):
    
    @action(detail=False, methods=['post'])
    def analyze_video(self, request):
        """Запуск анализа хромоты для видео"""
        try:
            video_id = request.data.get('video_id')
            if not video_id:
                return Response(
                    {'error': 'video_id обязателен'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Получаем видео из БД
            video = Video.objects.get(video_id=video_id)
            
            # Запускаем анализ в фоне
            threading.Thread(
                target=self._process_lameness_analysis, 
                args=(video_id,)
            ).start()
            
            return Response({
                'message': 'Анализ хромоты запущен',
                'video_id': video_id,
                'status': 'processing'
            })
            
        except Video.DoesNotExist:
            return Response(
                {'error': 'Видео не найдено'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Ошибка: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _process_lameness_analysis(self, video_id):
        """Фоновая обработка анализа хромоты"""
        try:
            video = Video.objects.get(video_id=video_id)
            
            # Инициализируем детектор из тестового скрипта
            # Используем ваш рабочий детектор
            detector = HorseLamenessDetector()
            
            # Получаем путь к видео файлу
            video_path = Path(video.file_path)
            
            if not video_path.exists():
                # Если файла нет по пути, пробуем найти в медиа
                media_path = Path('media') / video.file_path
                if media_path.exists():
                    video_path = media_path
                else:
                    print(f"Видео файл не найден: {video.file_path}")
                    return
            
            # Запускаем анализ (это займет время)
            print(f"Начинаем анализ видео: {video_path}")
            result = detector.process(video_path)
            
            if result:
                # Создаем или обновляем анализ в БД
                analysis, created = Analysis.objects.get_or_create(
                    video=video,
                    defaults={'analysis_date': timezone.now()}
                )
                
                # Обновляем поля хромоты
                analysis.is_lame = result.get('is_lame')
                analysis.lameness_probability = result.get('lameness_probability')
                analysis.lameness_confidence = result.get('confidence')
                analysis.diagnosis = result.get('diagnosis', '')
                analysis.diagnosis_note = result.get('diagnosis_note', '')
                analysis.analysis_date = timezone.now()
                analysis.save()
                
                print(f"Анализ хромоты завершен для видео {video_id}")
                
        except Exception as e:
            print(f"Ошибка анализа хромоты: {e}")
    
    @action(detail=False, methods=['get'])
    def analysis_status(self, request):
        """Получение статуса анализа"""
        video_id = request.query_params.get('video_id')
        if not video_id:
            return Response(
                {'error': 'video_id обязателен'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            video = Video.objects.get(video_id=video_id)
            analysis = Analysis.objects.filter(video=video).first()
            
            response_data = {
                'video_id': video_id,
                'has_analysis': analysis is not None
            }
            
            if analysis:
                response_data.update({
                    'is_lame': analysis.is_lame,
                    'lameness_probability': analysis.lameness_probability,
                    'confidence': analysis.lameness_confidence,
                    'diagnosis': analysis.diagnosis,
                    'diagnosis_note': analysis.diagnosis_note,
                    'analysis_date': analysis.analysis_date
                })
            
            return Response(response_data)
            
        except Video.DoesNotExist:
            return Response(
                {'error': 'Видео не найдено'}, 
                status=status.HTTP_404_NOT_FOUND
            )
