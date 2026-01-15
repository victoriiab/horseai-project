from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from web.database.models import Animal, User
from django.utils import timezone

@csrf_exempt
def add_animal_api(request):
    """Добавление животного через API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Требуется авторизация'})
    
    if request.method == 'POST':
        try:
            # Получаем данные
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            # Находим пользователя
            custom_user = User.objects.get(login=request.user.username)
            
            # Создаем животное
            animal = Animal.objects.create(
                user=custom_user,
                name=data.get('name', 'Без имени'),
                sex=data.get('sex', 'unknown'),
                age=int(data.get('age', 0)) if data.get('age') else None,
                estimated_weight=float(data.get('weight', 0)) if data.get('weight') else None,
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
