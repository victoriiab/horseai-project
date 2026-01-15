"""
Views для отображения анализов
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from database.models import Analysis, Video, Animal

@login_required
def analysis_list(request):
    """Список анализов пользователя"""
    analyses = Analysis.objects.filter(
        video__user=request.user
    ).select_related(
        'video', 'video__animal'
    ).order_by('-analysis_date')
    
    context = {
        'analyses': analyses,
        'total_count': analyses.count(),
        'lame_count': analyses.filter(is_lame=True).count(),
        'healthy_count': analyses.filter(is_lame=False).count(),
    }
    return render(request, 'frontend/analysis.html', context)

@login_required
def analysis_detail(request, analysis_id):
    """Детальная страница анализа"""
    analysis = get_object_or_404(
        Analysis, 
        analysis_id=analysis_id,
        video__user=request.user
    )
    
    context = {
        'analysis': analysis,
        'video': analysis.video,
        'animal': analysis.video.animal,
    }
    return render(request, 'frontend/analysis_detail.html', context)

@login_required
def ration_list(request):
    """Список рационов"""
    from database.models import Ration
    
    rations = Ration.objects.filter(
        animal__user=request.user
    ).select_related('animal', 'analysis').order_by('-calculation_date')
    
    context = {
        'rations': rations
    }
    return render(request, 'frontend/ration.html', context)
