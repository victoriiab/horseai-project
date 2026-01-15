"""
Простые тестовые views для отладки
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from web.database.models import Animal, Ration, User
from django.utils import timezone

def test_ration_page(request):
    """Простая тестовая страница расчета рациона"""
    return render(request, 'test_ration.html')

@csrf_exempt  # Отключаем CSRF для теста
def simple_calculate_ration(request):
    """Упрощенный API расчета рациона без CSRF"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body) if request.body else {}
            
            # Базовые параметры
            weight = float(data.get('weight', 500))
            animal_id = data.get('animal_id', 1)
            
            # Простой расчет
            dmi = weight * 0.025  # 2.5% от веса
            hay = dmi * 0.65 * (100/85)
            grain = dmi * 0.25 * (100/87)
            supplement = dmi * 0.08 * (100/88)
            vegetable = 2.0
            premix = 0.1
            
            # Пытаемся найти животное
            try:
                animal = Animal.objects.get(animal_id=animal_id)
                # Сохраняем в БД
                ration = Ration.objects.create(
                    animal=animal,
                    total_dmi=round(dmi, 2),
                    energy_content=round(dmi * 8.5, 1),
                    calculation_date=timezone.now(),
                    composition={
                        'hay': round(hay, 2),
                        'grain': round(grain, 2),
                        'supplement': round(supplement, 2),
                        'vegetable': round(vegetable, 2),
                        'premix': round(premix, 3)
                    }
                )
                ration_id = ration.ration_id
            except:
                ration_id = 0
            
            return JsonResponse({
                'success': True,
                'ration_id': ration_id,
                'total_dmi': round(dmi, 2),
                'energy_content': round(dmi * 8.5, 1),
                'feed_breakdown': {
                    'hay': round(hay, 2),
                    'oats': round(grain, 2),
                    'bran': round(supplement, 2),
                    'carrot': round(vegetable, 2),
                    'premix': round(premix * 1000, 0)
                },
                'recommendations': [
                    "Разделите суточную норму на 3-4 кормления",
                    "Сено должно быть доступно постоянно",
                    "Концентраты давайте после сена",
                    "Обеспечьте постоянный доступ к чистой воде"
                ],
                'message': 'Рацион успешно рассчитан!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Только POST'})
