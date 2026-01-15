
@login_required
@csrf_exempt
def calculate_ration_api(request):
    """API для расчета рациона кормления"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST метод'})
    
    try:
        import json
        data = json.loads(request.body)
        
        animal_id = data.get('animal_id')
        activity_level = data.get('activity_level', 'medium')  # low, medium, high
        include_supplements = data.get('include_supplements', True)
        
        if not animal_id:
            return JsonResponse({'success': False, 'error': 'Укажите ID животного'})
        
        # Получаем животное
        try:
            custom_user = User.objects.get(login=request.user.username)
            animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
        except (User.DoesNotExist, Animal.DoesNotExist):
            # Для теста используем любое животное
            animal = Animal.objects.filter(animal_id=animal_id).first()
            if not animal:
                return JsonResponse({'success': False, 'error': 'Животное не найдено'})
        
        # Базовые параметры
        weight = animal.estimated_weight or 500  # кг
        age = animal.age or 5  # лет
        
        # Коэффициенты активности
        activity_factors = {
            'low': 1.5,      # Легкая работа
            'medium': 2.0,   # Средняя нагрузка
            'high': 2.5      # Тяжелая работа
        }
        
        activity_factor = activity_factors.get(activity_level, 2.0)
        
        # Расчет потребностей
        maintenance_energy = weight * 0.033  # МДж/день на поддержание
        work_energy = maintenance_energy * activity_factor
        
        # Суточное потребление сухого вещества
        dry_matter_intake = weight * 0.025  # 2.5% от массы тела
        
        # Состав рациона (в кг)
        composition = {
            'сено_луговое': {
                'amount': round(dry_matter_intake * 0.6, 2),
                'energy': round(dry_matter_intake * 0.6 * 8.5, 2),
                'protein': round(dry_matter_intake * 0.6 * 0.10, 2),
                'cost': round(dry_matter_intake * 0.6 * 25 / 1000, 2)  # 25 руб/кг
            },
            'овес': {
                'amount': round(dry_matter_intake * 0.25, 2),
                'energy': round(dry_matter_intake * 0.25 * 11.5, 2),
                'protein': round(dry_matter_intake * 0.25 * 0.12, 2),
                'cost': round(dry_matter_intake * 0.25 * 40 / 1000, 2)  # 40 руб/кг
            },
            'отруби_пшеничные': {
                'amount': round(dry_matter_intake * 0.15, 2),
                'energy': round(dry_matter_intake * 0.15 * 10.0, 2),
                'protein': round(dry_matter_intake * 0.15 * 0.15, 2),
                'cost': round(dry_matter_intake * 0.15 * 35 / 1000, 2)  # 35 руб/кг
            }
        }
        
        # Добавки если нужно
        if include_supplements:
            composition['премикс_витаминный'] = {
                'amount': 0.1,
                'energy': 0.5,
                'protein': 0.02,
                'cost': 5.0
            }
            composition['соль_лизунец'] = {
                'amount': 0.05,
                'energy': 0,
                'protein': 0,
                'cost': 1.5
            }
        
        # Итоги
        total_amount = sum(item['amount'] for item in composition.values())
        total_energy = sum(item['energy'] for item in composition.values())
        total_protein = sum(item['protein'] for item in composition.values())
        total_cost = sum(item['cost'] for item in composition.values())
        
        # Создаем запись рациона в БД
        from web.database.models import Ration
        
        # Получаем последний анализ для животного
        last_analysis = Analysis.objects.filter(video__animal=animal).order_by('-analysis_date').first()
        
        ration = Ration.objects.create(
            animal=animal,
            analysis=last_analysis,
            total_dmi=total_amount,
            energy_content=total_energy,
            calculation_date=datetime.now(),
            composition=composition
        )
        
        response_data = {
            'success': True,
            'message': f'Рацион для {animal.name} рассчитан',
            'ration_id': ration.ration_id,
            'animal': {
                'name': animal.name,
                'weight': weight,
                'age': age,
                'sex': animal.sex
            },
            'parameters': {
                'activity_level': activity_level,
                'dry_matter_intake': round(dry_matter_intake, 2),
                'energy_requirement': round(work_energy, 2)
            },
            'composition': composition,
            'totals': {
                'amount_kg': round(total_amount, 2),
                'energy_mj': round(total_energy, 2),
                'protein_kg': round(total_protein, 2),
                'cost_rub': round(total_cost, 2)
            },
            'recommendations': [
                'Разделить на 3-4 кормления в день',
                'Обеспечить постоянный доступ к воде',
                'Контролировать упитанность животного',
                'Корректировать рацион при изменении нагрузки'
            ]
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"❌ Ошибка расчета рациона: {e}")
        return JsonResponse({'success': False, 'error': str(e)})
