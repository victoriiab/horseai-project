"""
Views для страниц анализа
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def analysis_detail_view(request, analysis_id):
    """Детальная страница анализа"""
    return render(request, 'frontend/analysis_detail.html', {
        'analysis_id': analysis_id,
        'user': request.user
    })

@login_required  
def video_management_view(request):
    """Страница управления видео"""
    return render(request, 'frontend/video_management.html', {
        'user': request.user
    })
