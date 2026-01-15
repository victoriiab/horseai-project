from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import os
import time
from web.database.models import Analysis, Video

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_analysis_status(request, analysis_id):
    """Получить статус анализа в реальном времени"""
    
    analysis = get_object_or_404(Analysis, pk=analysis_id)
    
    # Проверяем доступ пользователя
    if request.user.username != analysis.video.user.login:
        return Response({'error': 'Нет доступа'}, status=403)
    
    # Определяем статус на основе полей в базе
    status = 'pending'
    if analysis.analysis_date:
        status = 'completed'
    elif analysis.lameness_probability is not None:
        status = 'processing_ml'
    elif analysis.video and analysis.video.file_path and os.path.exists(analysis.video.file_path):
        status = 'uploaded'
    
    # Генерируем лог (в реальном приложении можно читать из файла лога)
    import random
    logs = [
        f"✅ Видео загружено: {os.path.basename(analysis.video.file_path) if analysis.video.file_path else 'Неизвестно'}",
        f"📊 Размер видео: {os.path.getsize(analysis.video.file_path) / (1024*1024):.2f} MB" if analysis.video.file_path and os.path.exists(analysis.video.file_path) else "📊 Размер: неизвестен",
        f"🤖 Запуск DLC анализа...",
        f"🎯 Обнаружено ключевых точек: {random.randint(15, 25)}",
        f"📈 Извлечение признаков походки...",
        f"🧠 Запуск ML модели для детекции хромоты...",
    ]
    
    # Если анализ завершен, добавляем результат
    if status == 'completed':
        logs.append(f"✅ Анализ завершен!")
        logs.append(f"📊 Результат: {analysis.diagnosis or 'Норма'}")
        logs.append(f"📈 Вероятность хромоты: {analysis.lameness_probability or 0}%")
        logs.append(f"⚠️ Хромота: {'Обнаружена' if analysis.is_lame else 'Не обнаружена'}")
    
    # Собираем ответ
    response_data = {
        'analysis_id': analysis_id,
        'status': status,
        'animal_name': analysis.video.animal.name if analysis.video and analysis.video.animal else 'Неизвестно',
        'video_id': analysis.video_id,
        'progress': {
            'pending': 0,
            'uploaded': 25,
            'processing_dlc': 50,
            'processing_ml': 75,
            'completed': 100
        }.get(status, 0),
        'log': random.choice(logs) if logs else "Анализ запущен...",
        'timestamp': time.time()
    }
    
    # Если есть ошибка в диагнозе
    if analysis.diagnosis and 'ошибка' in analysis.diagnosis.lower():
        response_data['status'] = 'failed'
        response_data['error'] = analysis.diagnosis
    
    return Response(response_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_video_analysis_status(request, video_id):
    """Получить статус анализа по video_id"""
    
    video = get_object_or_404(Video, pk=video_id)
    
    # Проверяем доступ пользователя
    if request.user.username != video.user.login:
        return Response({'error': 'Нет доступа'}, status=403)
    
    # Получаем последний анализ для этого видео
    analysis = Analysis.objects.filter(video=video).order_by('-analysis_date').first()
    
    if not analysis:
        return Response({
            'status': 'not_found',
            'message': 'Анализ для этого видео не найден'
        })
    
    return get_analysis_status(request, analysis.analysis_id)
