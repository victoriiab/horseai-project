"""
API для работы с рационами
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from web.database.models import Animal, Ration, User
from django.utils import timezone

@csrf_exempt
@login_required
def save_ration_api(request):
    """Сохранение рассчитанного рациона в БД"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST метод'})

    try:
        data = json.loads(request.body) if request.body else request.POST
        
        animal_id = data.get('animal_id')
        if not animal_id:
            return JsonResponse({'success': False, 'error': 'Не указано животное'})

        # Получаем пользователя и животное
        custom_user = User.objects.get(login=request.user.username)
        animal = get_object_or_404(Animal, animal_id=animal_id, user=custom_user)

        # Извлекаем данные из запроса
        weight = float(data.get('weight', 0))
        activity_level = data.get('activity_level', 'medium')
        health_status = data.get('health_status', 'healthy')
        goal = data.get('goal', 'maintain')
        breed_type = data.get('breed_type', 'medium')
        body_condition = data.get('body_condition', 'normal')
        has_lameness = data.get('has_lameness', False)
        
        # Данные кормов
        feed_prices = data.get('feed_prices', {})
        feed_amounts = data.get('feed_amounts', {})
        
        # Рассчитанные значения
        total_dmi = float(data.get('total_dmi', 0))
        energy_content = float(data.get('energy_content', 0))
        protein_amount = float(data.get('protein_amount', 0))
        fiber_amount = float(data.get('fiber_amount', 0))
        
        # Стоимость
        total_day_cost = float(data.get('total_day_cost', 0))
        total_month_cost = float(data.get('total_month_cost', 0))
        
        # Рекомендации
        recommendations = data.get('recommendations', [])
        
        # Создаем или обновляем рацион
        ration = Ration.objects.create(
            animal=animal,
            total_dmi=total_dmi,
            energy_content=energy_content,
            calculation_date=timezone.now(),
            created_at=timezone.now(),
            
            # Новые поля
            activity_level=activity_level,
            health_status=health_status,
            goal=goal,
            breed_type=breed_type,
            body_condition=body_condition,
            has_lameness=has_lameness,
            
            # JSON поля
            composition={
                'hay': feed_amounts.get('hay', 0),
                'grain': feed_amounts.get('grain', 0),
                'supplement': feed_amounts.get('supplement', 0),
                'vegetable': feed_amounts.get('vegetable', 0),
                'premix': feed_amounts.get('premix', 0)
            },
            feed_prices=feed_prices,
            feed_amounts=feed_amounts,
            recommendations=recommendations,
            
            # Дополнительные данные
            notes=f"Рацион для {animal.name}. Вес: {weight}кг. Хромота: {'да' if has_lameness else 'нет'}"
        )

        return JsonResponse({
            'success': True,
            'ration_id': ration.ration_id,
            'message': 'Рацион успешно сохранен в историю',
            'created_at': ration.created_at.strftime('%d.%m.%Y %H:%M')
        })

    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@login_required
def get_rations_api(request):
    """Получение истории рационов пользователя"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        
        # Получаем рационы пользователя
        rations = Ration.objects.filter(animal__user=custom_user).select_related('animal').order_by('-created_at')
        
        rations_data = []
        for ration in rations:
            rations_data.append({
                'id': ration.ration_id,
                'animal_name': ration.animal.name if ration.animal else 'Неизвестно',
                'animal_id': ration.animal.animal_id if ration.animal else None,
                'created_at': ration.created_at.strftime('%d.%m.%Y %H:%M'),
                'calculation_date': ration.calculation_date.strftime('%d.%m.%Y') if ration.calculation_date else '',
                'total_dmi': ration.total_dmi,
                'energy_content': ration.energy_content,
                'total_day_cost': ration.composition.get('total_cost', 0) if isinstance(ration.composition, dict) else 0,
                'has_lameness': ration.has_lameness or False,
                'activity_level': ration.activity_level or 'medium',
                'notes': ration.notes or ''
            })
        
        return JsonResponse({
            'success': True,
            'rations': rations_data,
            'count': len(rations_data)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_ration_detail_api(request, ration_id):
    """Получение детальной информации о рационе"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        
        # Находим рацион (проверяем доступ пользователя)
        ration = Ration.objects.get(
            ration_id=ration_id,
            animal__user=custom_user
        )
        
        # Формируем детальные данные
        data = {
            'id': ration.ration_id,
            'animal': {
                'id': ration.animal.animal_id,
                'name': ration.animal.name,
                'weight': ration.animal.estimated_weight
            },
            'created_at': ration.created_at.strftime('%d.%m.%Y %H:%M'),
            'parameters': {
                'activity_level': ration.activity_level,
                'health_status': ration.health_status,
                'goal': ration.goal,
                'breed_type': ration.breed_type,
                'body_condition': ration.body_condition,
                'has_lameness': ration.has_lameness
            },
            'nutrition': {
                'total_dmi': ration.total_dmi,
                'energy_content': ration.energy_content,
                'protein': (ration.total_dmi * 0.1) if ration.total_dmi else 0,
                'fiber': (ration.total_dmi * 0.6) if ration.total_dmi else 0
            },
            'feed_amounts': ration.feed_amounts if ration.feed_amounts else {},
            'feed_prices': ration.feed_prices if ration.feed_prices else {},
            'composition': ration.composition if ration.composition else {},
            'recommendations': ration.recommendations if ration.recommendations else [],
            'notes': ration.notes or ''
        }
        
        # Рассчитываем стоимость если есть данные
        if ration.feed_amounts and ration.feed_prices:
            total_day_cost = 0
            for feed_type, amount in ration.feed_amounts.items():
                price = ration.feed_prices.get(feed_type, 0)
                total_day_cost += amount * price
            
            data['cost'] = {
                'day': round(total_day_cost, 2),
                'month': round(total_day_cost * 30, 2)
            }
        
        return JsonResponse({'success': True, 'ration': data})

    except Ration.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Рацион не найден'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required
def delete_ration_api(request, ration_id):
    """Удаление рациона"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST метод'})

    try:
        custom_user = User.objects.get(login=request.user.username)
        
        # Находим и удаляем рацион
        ration = Ration.objects.get(
            ration_id=ration_id,
            animal__user=custom_user
        )
        
        ration.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Рацион успешно удален'
        })

    except Ration.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Рацион не найден'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
