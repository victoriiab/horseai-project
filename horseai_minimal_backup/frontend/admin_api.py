"""
ADMIN API ДЛЯ СУПЕРАДМИНА
"""

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from datetime import datetime, timedelta
from web.database.models import User, Animal, Video, Analysis, Ration

@login_required
@staff_member_required
def admin_stats_api(request):
    """Статистика для админ-панели"""
    try:
        # Проверяем, что пользователь - админ
        custom_user = User.objects.get(login=request.user.username)
        is_admin = request.user.is_staff or custom_user.role_id in ['admin', 'superadmin']
        
        if not is_admin:
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
        
        # Собираем статистику
        from django.db.models import Count, Avg, Q
        
        # Общая статистика
        stats = {
            'users': {
                'total': User.objects.count(),
                'active': User.objects.filter(is_active=True).count(),
                'admins': User.objects.filter(role_id__in=['admin', 'superadmin']).count(),
                'new_today': User.objects.filter(created_at__date=datetime.now().date()).count(),
            },
            'animals': {
                'total': Animal.objects.count(),
                'with_videos': Animal.objects.annotate(video_count=Count('video')).filter(video_count__gt=0).count(),
            },
            'videos': {
                'total': Video.objects.count(),
                'analyzed': Video.objects.filter(analysis_status='completed').count(),
                'pending': Video.objects.filter(analysis_status='uploaded').count(),
            },
            'analyses': {
                'total': Analysis.objects.count(),
                'lame': Analysis.objects.filter(is_lame=True).count(),
                'healthy': Analysis.objects.filter(is_lame=False).count(),
                'avg_confidence': Analysis.objects.aggregate(avg=Avg('confidence_score'))['avg'] or 0,
            },
            'system': {
                'timestamp': datetime.now().isoformat(),
                'last_24h_uploads': Video.objects.filter(upload_date__gte=datetime.now()-timedelta(days=1)).count(),
                'last_week_analyses': Analysis.objects.filter(analysis_date__gte=datetime.now()-timedelta(days=7)).count(),
            }
        }
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'user': {
                'username': request.user.username,
                'role': custom_user.role_id,
                'is_staff': request.user.is_staff
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@staff_member_required
def admin_analyses_api(request):
    """Список анализов для админ-панели"""
    try:
        # Проверяем права
        custom_user = User.objects.get(login=request.user.username)
        is_admin = request.user.is_staff or custom_user.role_id in ['admin', 'superadmin']
        
        if not is_admin:
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
        
        # Параметры пагинации
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        offset = (page - 1) * page_size
        
        # Фильтры
        filter_lame = request.GET.get('lame')
        filter_animal = request.GET.get('animal_id')
        filter_user = request.GET.get('user_id')
        
        # Базовый запрос
        analyses = Analysis.objects.select_related('video', 'video__animal', 'video__user')
        
        # Применяем фильтры
        if filter_lame is not None:
            analyses = analyses.filter(is_lame=(filter_lame.lower() == 'true'))
        if filter_animal:
            analyses = analyses.filter(video__animal_id=filter_animal)
        if filter_user:
            analyses = analyses.filter(video__user_id=filter_user)
        
        # Сортировка и пагинация
        total_count = analyses.count()
        analyses = analyses.order_by('-analysis_date')[offset:offset + page_size]
        
        # Формируем ответ
        analyses_list = []
        for analysis in analyses:
            analyses_list.append({
                'id': analysis.analysis_id,
                'video_id': analysis.video.video_id if analysis.video else None,
                'animal': {
                    'id': analysis.video.animal.animal_id if analysis.video and analysis.video.animal else None,
                    'name': analysis.video.animal.name if analysis.video and analysis.video.animal else 'Неизвестно'
                },
                'user': {
                    'id': analysis.video.user.user_id if analysis.video and analysis.video.user else None,
                    'login': analysis.video.user.login if analysis.video and analysis.video.user else 'Неизвестно'
                },
                'is_lame': analysis.is_lame,
                'lameness_probability': analysis.lameness_probability,
                'confidence': analysis.confidence_score,
                'diagnosis': analysis.diagnosis or 'Нет диагноза',
                'analysis_date': analysis.analysis_date.strftime('%Y-%m-%d %H:%M:%S') if analysis.analysis_date else None,
                'created': analysis.analysis_date.strftime('%d.%m.%Y') if analysis.analysis_date else None
            })
        
        return JsonResponse({
            'success': True,
            'analyses': analyses_list,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@staff_member_required
@csrf_exempt
def update_analysis_api(request, analysis_id):
    """Обновление анализа (админ)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST метод'}, status=405)
    
    try:
        # Проверяем права
        custom_user = User.objects.get(login=request.user.username)
        is_admin = request.user.is_staff or custom_user.role_id in ['admin', 'superadmin']
        
        if not is_admin:
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
        
        analysis = get_object_or_404(Analysis, analysis_id=analysis_id)
        data = json.loads(request.body)
        
        # Обновляем поля
        if 'is_lame' in data:
            analysis.is_lame = bool(data['is_lame'])
        if 'lameness_probability' in data:
            analysis.lameness_probability = float(data['lameness_probability'])
        if 'diagnosis' in data:
            analysis.diagnosis = data['diagnosis']
        if 'diagnosis_note' in data:
            analysis.diagnosis_note = data['diagnosis_note']
        if 'confidence' in data:
            analysis.confidence_score = float(data['confidence'])
        
        analysis.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Анализ обновлен',
            'analysis': {
                'id': analysis.analysis_id,
                'is_lame': analysis.is_lame,
                'probability': analysis.lameness_probability,
                'diagnosis': analysis.diagnosis
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@staff_member_required
@csrf_exempt
def delete_analysis_api(request, analysis_id):
    """Удаление анализа (админ)"""
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Только DELETE метод'}, status=405)
    
    try:
        # Проверяем права
        custom_user = User.objects.get(login=request.user.username)
        is_admin = request.user.is_staff or custom_user.role_id in ['admin', 'superadmin']
        
        if not is_admin:
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
        
        analysis = get_object_or_404(Analysis, analysis_id=analysis_id)
        analysis_id_val = analysis.analysis_id
        analysis.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Анализ #{analysis_id_val} удален'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
