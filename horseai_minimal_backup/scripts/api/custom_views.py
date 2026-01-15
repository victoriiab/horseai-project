from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from web.database.models import Animal, User, Ration
import json
from datetime import datetime

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def animal_list(request):
    """Список животных пользователя"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        animals = Animal.objects.filter(user=custom_user)
        
        data = []
        for animal in animals:
            data.append({
                'animal_id': animal.animal_id,
                'name': animal.name,
                'sex': animal.sex,
                'age': animal.age,
                'estimated_weight': animal.estimated_weight,
                'created_at': animal.created_at,
            })
        
        return Response({
            'success': True,
            'animals': data,
            'count': len(data)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def animal_create(request):
    """Создание животного"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        
        animal = Animal.objects.create(
            user=custom_user,
            name=request.data.get('name', 'Новая лошадь'),
            sex=request.data.get('sex'),
            age=request.data.get('age'),
            estimated_weight=request.data.get('estimated_weight'),
            created_at=datetime.now()
        )
        
        return Response({
            'success': True,
            'message': 'Животное создано',
            'animal_id': animal.animal_id
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def animal_detail(request, animal_id):
    """Детали животного"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        animal = get_object_or_404(Animal, pk=animal_id, user=custom_user)
        
        # Получаем связанные видео
        videos = animal.video_set.all()
        videos_data = []
        for video in videos:
            videos_data.append({
                'video_id': video.video_id,
                'file_path': video.file_path,
                'upload_date': video.upload_date,
                'duration': video.duration,
                'resolution': video.resolution,
                'analysis_status': video.analysis_status,
            })
        
        # Получаем связанные рационы
        rations = animal.ration_set.all()
        rations_data = []
        for ration in rations:
            rations_data.append({
                'ration_id': ration.ration_id,
                'total_dmi': ration.total_dmi,
                'energy_content': ration.energy_content,
                'calculation_date': ration.calculation_date,
                'composition': ration.composition,
            })
        
        return Response({
            'success': True,
            'animal': {
                'animal_id': animal.animal_id,
                'name': animal.name,
                'sex': animal.sex,
                'age': animal.age,
                'estimated_weight': animal.estimated_weight,
                'created_at': animal.created_at,
                'videos': videos_data,
                'videos_count': len(videos_data),
                'rations': rations_data,
                'rations_count': len(rations_data),
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@permission_classes([IsAuthenticated])
def animal_delete(request, animal_id):
    """Удаление животного"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        animal = get_object_or_404(Animal, pk=animal_id, user=custom_user)
        
        animal_id_copy = animal.animal_id
        animal.delete()
        
        return Response({
            'success': True,
            'message': f'Животное #{animal_id_copy} удалено'
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_ration(request):
    """Расчет рациона"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        animal_id = request.data.get('animal_id')
        
        if not animal_id:
            return Response({
                'success': False,
                'error': 'Не указан animal_id'
            }, status=400)
        
        animal = get_object_or_404(Animal, pk=animal_id, user=custom_user)
        
        # Базовая логика расчета (упрощенная)
        weight = animal.estimated_weight or 500  # кг
        total_dmi = weight * 0.02  # 2% от массы тела
        energy_content = total_dmi * 2000  # примерная энергия
        
        # Примерный состав
        composition = {
            'hay': {
                'name': 'Сено луговое',
                'type': 'hay',
                'quantity': total_dmi * 0.7,  # 70%
                'dry_matter': 85,
                'energy': 1800,
                'protein': 8,
                'fiber': 30
            },
            'concentrate': {
                'name': 'Концентрат зерновой',
                'type': 'concentrate',
                'quantity': total_dmi * 0.25,  # 25%
                'dry_matter': 90,
                'energy': 2800,
                'protein': 12,
                'fiber': 10
            },
            'additives': {
                'name': 'Минеральные добавки',
                'type': 'additive',
                'quantity': total_dmi * 0.05,  # 5%
                'dry_matter': 95,
                'energy': 1000,
                'protein': 0,
                'fiber': 0
            }
        }
        
        # Создаем рацион
        ration = Ration.objects.create(
            animal=animal,
            total_dmi=round(total_dmi, 2),
            energy_content=round(energy_content, 0),
            calculation_date=datetime.now(),
            composition=composition
        )
        
        return Response({
            'success': True,
            'message': 'Рацион рассчитан',
            'ration_id': ration.ration_id,
            'total_dmi': ration.total_dmi,
            'energy_content': ration.energy_content,
            'composition': ration.composition
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def animal_update(request, animal_id):
    """Обновление животного - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        animal = get_object_or_404(Animal, pk=animal_id, user=custom_user)
        
        # Логируем что пришло
        print(f"UPDATE request for animal {animal_id}: {request.data}")
        
        # Обновляем поля
        updated_fields = []
        
        if 'name' in request.data:
            animal.name = request.data['name']
            updated_fields.append('name')
            print(f"  -> name = {request.data['name']}")
        
        # ВАЖНО: проверяем что значение не пустое
        if 'age' in request.data and request.data['age'] not in ['', None]:
            animal.age = int(request.data['age'])
            updated_fields.append('age')
            print(f"  -> age = {request.data['age']}")
        
        if 'estimated_weight' in request.data and request.data['estimated_weight'] not in ['', None]:
            animal.estimated_weight = float(request.data['estimated_weight'])
            updated_fields.append('weight')
            print(f"  -> weight = {request.data['estimated_weight']}")
        
        if 'sex' in request.data:
            animal.sex = request.data['sex']
            updated_fields.append('sex')
            print(f"  -> sex = {request.data['sex']}")
        
        animal.save()
        
        return Response({
            'success': True,
            'message': f'Животное обновлено. Изменены: {", ".join(updated_fields)}',
            'animal_id': animal.animal_id,
            'updated_fields': updated_fields
        })
        
    except Exception as e:
        print(f"UPDATE ERROR: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
