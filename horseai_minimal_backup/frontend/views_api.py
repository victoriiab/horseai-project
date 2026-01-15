"""
API views для фронтенда - работают через AJAX
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
from web.database.models import Animal, User

@csrf_exempt
@login_required
@require_POST
def api_add_animal(request):
    """API: Добавление животного"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Имя животного обязательно'})
        
        custom_user = User.objects.get(login=request.user.username)
        
        animal = Animal.objects.create(
            user=custom_user,
            name=name,
            sex=data.get('sex', ''),
            age=data.get('age'),
            estimated_weight=data.get('weight'),
            created_at=request.user.date_joined
        )
        
        return JsonResponse({
            'success': True,
            'animal_id': animal.animal_id,
            'message': f'Животное "{name}" добавлено'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required
@require_GET
def api_user_animals(request):
    """API: Список животных пользователя"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        animals = Animal.objects.filter(user=custom_user).order_by('-created_at')
        
        animals_list = []
        for animal in animals:
            animals_list.append({
                'id': animal.animal_id,
                'name': animal.name,
                'sex': animal.sex or 'не указан',
                'age': animal.age or 'не указан',
                'weight': animal.estimated_weight or 'не указан',
                'created_at': animal.created_at.strftime('%d.%m.%Y') if animal.created_at else 'не указано'
            })
        
        return JsonResponse({
            'success': True,
            'animals': animals_list,
            'count': len(animals_list)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required
@require_POST
def api_update_animal(request, animal_id):
    """API: Обновление животного"""
    try:
        data = json.loads(request.body)
        custom_user = User.objects.get(login=request.user.username)
        
        animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
        
        if 'name' in data and data['name'].strip():
            animal.name = data['name'].strip()
        if 'sex' in data:
            animal.sex = data['sex']
        if 'age' in data:
            animal.age = data['age']
        if 'weight' in data:
            animal.estimated_weight = data['weight']
        
        animal.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Данные обновлены'
        })
    except Animal.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Животное не найдено'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required
@require_POST
def api_delete_animal(request, animal_id):
    """API: Удаление животного"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
        animal_name = animal.name
        animal.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Животное "{animal_name}" удалено'
        })
    except Animal.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Животное не найдено'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required
@require_GET
def api_animal_detail(request, animal_id):
    """API: Детали животного"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
        
        return JsonResponse({
            'success': True,
            'animal': {
                'id': animal.animal_id,
                'name': animal.name,
                'sex': animal.sex or '',
                'age': animal.age,
                'weight': animal.estimated_weight,
                'created_at': animal.created_at.strftime('%d.%m.%Y %H:%M') if animal.created_at else ''
            }
        })
    except Animal.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Животное не найдено'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
