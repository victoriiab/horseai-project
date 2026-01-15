"""
Упрощенные API views для сохранения рационов
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
def api_save_ration_simple(request):
    """Простой API для сохранения рациона"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST метод'})

    try:
        # Получаем данные
        data = json.loads(request.body) if request.body else {}
        
        animal_id = data.get('animal_id')
        if not animal_id:
            return JsonResponse({'success': False, 'error': 'Не указано животное'})

        # Получаем пользователя и животное
        custom_user = User.objects.get(login=request.user.username)
        animal = get_object_or_404(Animal, animal_id=animal_id, user=custom_user)

        # Создаем запись в БД
        ration = Ration.objects.create(
            animal=animal,
            total_dmi=float(data.get('total_dmi', 0)),
            energy_content=float(data.get('energy_content', 0)),
            calculation_date=timezone.now(),
            composition=data.get('composition', '{}')
        )

        return JsonResponse({
            'success': True,
            'ration_id': ration.ration_id,
            'message': 'Рацион успешно сохранен'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def api_user_rations_simple(request):
    """Простой API для получения рационов пользователя"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        
        # Получаем животных пользователя
        user_animals = Animal.objects.filter(user=custom_user)
        # Получаем рационы
        rations = Ration.objects.filter(animal__in=user_animals).order_by('-calculation_date')
        
        rations_data = []
        for ration in rations:
            try:
                composition = json.loads(ration.composition) if isinstance(ration.composition, str) else ration.composition
            except:
                composition = {}
            
            rations_data.append({
                'id': ration.ration_id,
                'animal_id': ration.animal.animal_id,
                'animal_name': ration.animal.name,
                'weight': composition.get('weight', '500'),
                'total_dmi': ration.total_dmi,
                'energy_content': ration.energy_content,
                'total_cost': float(composition.get('total_month_cost', 0)),
                'date': ration.calculation_date.strftime('%d.%m.%Y %H:%M'),
                'has_lameness': bool(composition.get('has_lameness', False)),
                'notes': 'Реабилитационный' if composition.get('has_lameness') else 'Обычный'
            })
        
        return JsonResponse({
            'success': True,
            'rations': rations_data,
            'count': len(rations_data)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
