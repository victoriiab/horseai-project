"""
Views для Super Admin панели
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from web.database.models import User, Animal, Video, Analysis
from django.db.models import Count, Q
from datetime import datetime, timedelta

def is_super_admin(user):
    """Проверка, является ли пользователь супер-администратором"""
    if not user.is_authenticated:
        return False
    
    try:
        custom_user = User.objects.get(login=user.username)
        return user.is_staff or custom_user.role_id in ['admin', 'superadmin']
    except User.DoesNotExist:
        return user.is_staff

@login_required
@user_passes_test(is_super_admin)
def super_admin_dashboard(request):
    """Super Admin панель"""
    try:
        # Базовая статистика
        total_users = User.objects.count()
        total_animals = Animal.objects.count()
        total_videos = Video.objects.count()
        total_analyses = Analysis.objects.count()
        
        # Активные пользователи (за последние 30 дней)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        active_users = User.objects.filter(last_login__gte=thirty_days_ago).count()
        
        # Обработанные видео
        processed_videos = Video.objects.filter(analysis_status='completed').count()
        
        # Хромота
        lame_count = Analysis.objects.filter(is_lame=True).count()
        healthy_count = Analysis.objects.filter(is_lame=False).count()
        
        # Последние 5 пользователей
        recent_users = User.objects.order_by('-created_at')[:5]
        
        # Последние 10 анализов
        recent_analyses = Analysis.objects.select_related(
            'video', 'video__animal', 'video__user'
        ).order_by('-analysis_date')[:10]
        
        context = {
            'stats': {
                'total_users': total_users,
                'active_users': active_users,
                'total_animals': total_animals,
                'total_videos': total_videos,
                'processed_videos': processed_videos,
                'total_analyses': total_analyses,
                'lame_count': lame_count,
                'healthy_count': healthy_count,
            },
            'recent_users': recent_users,
            'recent_analyses': recent_analyses,
            'page_title': 'Super Admin Panel',
            'user': request.user
        }
        
        return render(request, 'frontend/super_admin.html', context)
        
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f'Ошибка загрузки Super Admin панели: {str(e)}')
        from django.shortcuts import redirect
        return redirect('index')
