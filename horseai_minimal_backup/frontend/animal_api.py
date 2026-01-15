from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from web.database.models import Animal, User
from django.utils import timezone

@csrf_exempt
@login_required
def add_animal_api(request):
    """Добавление животного через API"""
    if request.method == 'POST':
        try:
            # Получаем данные
            data = json.loads(request.body)
            
            # Находим пользователя
            custom_user = User.objects.get(login=request.user.username)
            
            # Создаем животное
            animal = Animal.objects.create(
                user=custom_user,
                name=data.get('name', 'Без имени'),
                sex=data.get('sex', ''),
                age=int(data.get('age')) if data.get('age') else None,
                estimated_weight=float(data.get('weight')) if data.get('weight') else None,
                created_at=timezone.now()
            )
            
            return JsonResponse({
                'success': True, 
                'animal_id': animal.animal_id,
                'name': animal.name,
                'message': 'Животное успешно добавлено'
            })
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Пользователь не найден'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})

@login_required
def get_animal_api(request, animal_id):
    """Получение информации о животном"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
        
        return JsonResponse({
            'success': True,
            'animal_id': animal.animal_id,
            'name': animal.name,
            'sex': animal.sex or '',
            'age': animal.age,
            'estimated_weight': animal.estimated_weight,
            'created_at': animal.created_at.strftime('%d.%m.%Y')
        })
        
    except Animal.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Животное не найдено'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Пользователь не найден'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required
def update_animal_api(request, animal_id):
    """Обновление животного"""
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            custom_user = User.objects.get(login=request.user.username)
            animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
            
            # Обновляем поля
            animal.name = data.get('name', animal.name)
            animal.sex = data.get('sex', animal.sex)
            animal.age = int(data.get('age')) if data.get('age') else animal.age
            animal.estimated_weight = float(data.get('weight')) if data.get('weight') else animal.estimated_weight
            animal.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Животное обновлено'
            })
            
        except Animal.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Животное не найдено'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})

@csrf_exempt
@login_required
def delete_animal_api(request, animal_id):
    """Удаление животного"""
    if request.method == 'DELETE':
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
    
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})

@login_required
def list_animals_api(request):
    """Список животных пользователя"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        animals = Animal.objects.filter(user=custom_user).values(
            'animal_id', 'name', 'sex', 'age', 'estimated_weight', 'created_at'
        )
        
        animals_list = list(animals)
        
        return JsonResponse({
            'success': True,
            'animals': animals_list,
            'count': len(animals_list)
        })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Пользователь не найден'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
