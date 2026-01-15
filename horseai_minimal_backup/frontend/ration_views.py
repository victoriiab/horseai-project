"""
Views для управления рационами в Super Admin панели
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from web.database.models import Ration, Animal, User, Analysis
from django.core.paginator import Paginator
from django.db.models import Q
import json

@staff_member_required
@require_http_methods(["GET"])
def super_admin_rations(request):
    """Получить все рационы для Super Admin"""
    try:
        # Параметры фильтрации
        page = int(request.GET.get('page', 1))
        search = request.GET.get('search', '')
        animal_id = request.GET.get('animal_id', '')
        
        # Базовый запрос
        rations = Ration.objects.select_related(
            'animal', 
            'animal__user',
            'analysis'
        ).all().order_by('-calculation_date')
        
        # Применяем фильтры
        if search:
            rations = rations.filter(
                Q(animal__name__icontains=search) |
                Q(animal__user__full_name__icontains=search) |
                Q(composition__icontains=search)
            )
        
        if animal_id and animal_id.isdigit():
            rations = rations.filter(animal_id=int(animal_id))
        
        # Пагинация
        paginator = Paginator(rations, 20)
        page_obj = paginator.get_page(page)
        
        # Формируем данные для ответа
        rations_data = []
        for ration in page_obj:
            animal_weight = ration.animal.estimated_weight if ration.animal else None
            
            rations_data.append({
                'ration_id': ration.ration_id,
                'calculation_date': ration.calculation_date.isoformat() if ration.calculation_date else None,
                'animal_id': ration.animal.animal_id if ration.animal else None,
                'animal_name': ration.animal.name if ration.animal else 'Не указано',
                'animal_weight': animal_weight,
                'owner_id': ration.animal.user.user_id if ration.animal and ration.animal.user else None,
                'owner_name': ration.animal.user.full_name if ration.animal and ration.animal.user else None,
                'owner_login': ration.animal.user.login if ration.animal and ration.animal.user else None,
                'total_dmi': ration.total_dmi,
                'energy_content': ration.energy_content,
                'composition': ration.composition or {},
                'analysis_id': ration.analysis.analysis_id if ration.analysis else None,
            })
        
        # Получаем список животных для фильтра
        animals = Animal.objects.all().values('animal_id', 'name')[:50]
        
        return JsonResponse({
            'success': True,
            'rations': rations_data,
            'animals': list(animals),
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_count': paginator.count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка загрузки рационов: {str(e)}'
        }, status=500)

@staff_member_required
@require_http_methods(["GET"])
def super_admin_ration_detail(request, ration_id):
    """Получить детальную информацию о рационе"""
    try:
        ration = Ration.objects.select_related(
            'animal', 
            'animal__user',
            'analysis'
        ).get(ration_id=ration_id)
        
        # Связанный анализ
        analysis_data = None
        if ration.analysis:
            analysis_data = {
                'analysis_id': ration.analysis.analysis_id,
                'diagnosis': ration.analysis.diagnosis,
                'is_lame': ration.analysis.is_lame,
                'lameness_probability': ration.analysis.lameness_probability,
                'confidence': ration.analysis.lameness_confidence,
            }
        
        response_data = {
            'success': True,
            'ration': {
                'ration_id': ration.ration_id,
                'calculation_date': ration.calculation_date.isoformat() if ration.calculation_date else None,
                'animal_id': ration.animal.animal_id,
                'animal_name': ration.animal.name if ration.animal else 'Не указано',
                'animal_weight': ration.animal.estimated_weight if ration.animal else None,
                'owner_id': ration.animal.user.user_id if ration.animal and ration.animal.user else None,
                'owner_name': ration.animal.user.full_name if ration.animal and ration.animal.user else None,
                'owner_login': ration.animal.user.login if ration.animal and ration.animal.user else None,
                'total_dmi': ration.total_dmi,
                'energy_content': ration.energy_content,
                'composition': ration.composition or {},
                'analysis': analysis_data,
            }
        }
        
        return JsonResponse(response_data)
        
    except Ration.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Рацион не найден'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка загрузки рациона: {str(e)}'
        }, status=500)

@staff_member_required
@require_http_methods(["DELETE"])
def super_admin_delete_ration(request, ration_id):
    """Удалить рацион"""
    try:
        ration = Ration.objects.get(ration_id=ration_id)
        ration.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Рацион успешно удален'
        })
        
    except Ration.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Рацион не найден'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка удаления рациона: {str(e)}'
        }, status=500)

@staff_member_required
@require_http_methods(["POST"])
def super_admin_recalculate_ration(request, ration_id):
    """Пересчитать рацион"""
    try:
        ration = Ration.objects.get(ration_id=ration_id)
        
        # Здесь должна быть логика пересчета
        # Пока просто возвращаем успех
        return JsonResponse({
            'success': True,
            'message': 'Рацион пересчитан (заглушка)',
            'ration_id': ration_id
        })
        
    except Ration.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Рацион не найден'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка пересчета рациона: {str(e)}'
        }, status=500)
