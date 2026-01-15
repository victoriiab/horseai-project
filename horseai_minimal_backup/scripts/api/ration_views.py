"""
API для управления рационами - ИСПРАВЛЕННАЯ ВЕРСИЯ (без is_active)
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json
from web.database.models import Ration, Animal, User, Analysis

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_save_ration(request):
    """Сохранение рациона через API - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        # Получаем пользователя
        custom_user = User.objects.get(login=request.user.username)
        
        # Парсим данные
        data = json.loads(request.body)
        
        # Проверяем обязательные поля
        if not data.get('animal_id'):
            return JsonResponse({
                'success': False,
                'error': 'Не указана лошадь'
            }, status=400)
        
        # Получаем животное
        try:
            animal = Animal.objects.get(
                animal_id=data['animal_id'],
                user=custom_user
            )
        except Animal.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Лошадь не найдена'
            }, status=404)
        
        # Создаем состав рациона
        composition = {
            'hay_amount': data.get('hay_amount', 0),
            'grain_amount': data.get('grain_amount', 0),
            'supplement_amount': data.get('supplement_amount', 0),
            'vegetable_amount': data.get('vegetable_amount', 0),
            'premix_amount': data.get('premix_amount', 0),
            'hay_cost': data.get('hay_cost', 0),
            'grain_cost': data.get('grain_cost', 0),
            'supplement_cost': data.get('supplement_cost', 0),
            'vegetable_cost': data.get('vegetable_cost', 0),
            'premix_cost': data.get('premix_cost', 0),
            'total_day_cost': data.get('total_day_cost', 0),
            'total_month_cost': data.get('total_month_cost', 0),
            'lameness': data.get('lameness', 'none'),
            'lameness_duration': data.get('lameness_duration', ''),
            'supplements': data.get('supplements', []),
            'recommendations': data.get('recommendations', []),
            'protein': data.get('protein', 0),
            'fiber': data.get('fiber', 0),
        }
        
        # Создаем рацион - БЕЗ поля is_active
        ration = Ration.objects.create(
            animal=animal,
            total_dmi=data.get('total_dmi', 0),
            energy_content=data.get('energy', 0),
            calculation_date=timezone.now(),
            composition=composition
            # Убрано: is_active=True - этого поля нет в модели!
        )
        
        return JsonResponse({
            'success': True,
            'id': ration.ration_id,
            'message': 'Рацион сохранен'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат данных'
        }, status=400)
    except Exception as e:
        print(f"Ошибка сохранения рациона: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Ошибка сервера: {str(e)}'
        }, status=500)

@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def api_delete_ration(request, ration_id):
    """Удаление рациона через API"""
    try:
        # Получаем пользователя
        custom_user = User.objects.get(login=request.user.username)
        
        # Получаем рацион, проверяя принадлежность
        ration = Ration.objects.get(
            ration_id=ration_id,
            animal__user=custom_user
        )
        
        # Удаляем
        ration.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Рацион удален'
        })
        
    except Ration.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Рацион не найден'
        }, status=404)
    except Exception as e:
        print(f"Ошибка удаления рациона: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Ошибка сервера: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def api_get_user_rations(request):
    """Получение всех рационов пользователя"""
    try:
        # Получаем пользователя
        custom_user = CustomUser.objects.get(login=request.user.username)
        
        # Получаем рационы
        rations = Ration.objects.filter(animal__user=custom_user).order_by('-calculation_date')
        
        # Формируем ответ
        rations_data = []
        for ration in rations:
            rations_data.append({
                'id': ration.ration_id,
                'animal_id': ration.animal.animal_id,
                'animal_name': ration.animal.name,
                'calculation_date': ration.calculation_date.strftime('%d.%m.%Y %H:%M'),
                'total_dmi': ration.total_dmi,
                'total_cost': ration.composition.get('total_month_cost', 0) if ration.composition else 0,
                # Убрано: 'is_active': ration.is_active - этого поля нет
                'lameness': ration.composition.get('lameness', 'none') if ration.composition else 'none'
            })
        
        return JsonResponse({
            'success': True,
            'rations': rations_data
        })
        
    except Exception as e:
        print(f"Ошибка получения рационов: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Ошибка сервера: {str(e)}'
        }, status=500)
