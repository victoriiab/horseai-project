"""
VIEWS ДЛЯ СТАТУСА АНАЛИЗА
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from web.database.models import Video, Analysis

@login_required
def analysis_status(request):
    """Страница статуса анализа"""
    video_id = request.GET.get('video_id')
    analysis_id = request.GET.get('analysis_id')
    
    context = {}
    
    if video_id:
        try:
            video = Video.objects.get(pk=video_id)
            context['video'] = video
            
            # Ищем последний анализ
            analysis = Analysis.objects.filter(video=video).order_by('-analysis_date').first()
            if analysis:
                context['analysis'] = analysis
        except:
            pass
    
    elif analysis_id:
        try:
            analysis = Analysis.objects.get(pk=analysis_id)
            context['analysis'] = analysis
            context['video'] = analysis.video
        except:
            pass
    
    return render(request, 'frontend/analysis_status.html', context)
