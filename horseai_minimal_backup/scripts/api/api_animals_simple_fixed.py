"""
ИСПРАВЛЕННЫЙ ПРОСТОЙ API для животных
С исправлением ошибки created_at
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
import json

# Импортируем только то, что точно есть
try:
    from web.database.models import Animal, User, Video, Analysis
    HAS_MODELS = True
except ImportError:
    try:
        from database.models import Animal, User, Video, Analysis
        HAS_MODELS = True
    except ImportError:
        HAS_MODELS = False
        print("⚠️ Модели не импортированы в api_animals_simple.py")

# ========== ПРОСТЫЕ API ENDPOINTS ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def simple_animal_list(request):
    """Список животных текущего пользователя - ПРОСТОЙ"""
    if not HAS_MODELS:
        return Response({
            'success': False,
            'error': 'Модели не доступны'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        # Находим кастомного пользователя
        custom_user = User.objects.get(login=request.user.username)

        # Получаем животных пользователя
        animals = Animal.objects.filter(user=custom_user).order_by('-created_at')

        # Формируем простой ответ
        data = []
        for animal in animals:
            data.append({
                'animal_id': animal.animal_id,
                'name': animal.name,
                'sex': animal.sex,
                'age': animal.age,
                'estimated_weight': animal.estimated_weight,
                'created_at': animal.created_at.isoformat() if animal.created_at else None,
                'user_name': animal.user.full_name if animal.user else None,
            })

        return Response({
            'success': True,
            'animals': data,
            'total': len(data)
        })

    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Пользователь не найден'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simple_animal_create(request):
    """Создание животного - ПРОСТОЙ"""
    if not HAS_MODELS:
        return Response({
            'success': False,
            'error': 'Модели не доступны'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        # Находим кастомного пользователя
        custom_user = User.objects.get(login=request.user.username)

        # Проверяем обязательные поля
        name = request.data.get('name', '').strip()
        if not name or len(name) < 2:
            return Response({
                'success': False,
                'error': 'Имя животного должно содержать минимум 2 символа'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Создаем животное с указанием created_at
        animal = Animal.objects.create(
            user=custom_user,
            name=name,
            sex=request.data.get('sex'),
            age=request.data.get('age'),
            estimated_weight=request.data.get('estimated_weight'),
            created_at=timezone.now()  # ЯВНО указываем дату создания
        )

        return Response({
            'success': True,
            'message': 'Животное добавлено',
            'animal_id': animal.animal_id,
            'name': animal.name,
            'created_at': animal.created_at.isoformat() if animal.created_at else None
        })

    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Пользователь не найден'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Ошибка при создании: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def simple_animal_detail(request, animal_id):
    """Получение информации о животном - ПРОСТОЙ"""
    if not HAS_MODELS:
        return Response({
            'success': False,
            'error': 'Модели не доступны'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        # Находим кастомного пользователя
        custom_user = User.objects.get(login=request.user.username)

        # Получаем животное (только свое!)
        animal = get_object_or_404(Animal, animal_id=animal_id, user=custom_user)

        # Получаем связанные данные
        video_count = Video.objects.filter(animal=animal).count()
        analysis_count = Analysis.objects.filter(video__animal=animal).count()

        return Response({
            'success': True,
            'animal': {
                'animal_id': animal.animal_id,
                'name': animal.name,
                'sex': animal.sex,
                'age': animal.age,
                'estimated_weight': animal.estimated_weight,
                'created_at': animal.created_at.isoformat() if animal.created_at else None,
                'user_name': animal.user.full_name if animal.user else None,
                'video_count': video_count,
                'analysis_count': analysis_count
            }
        })

    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Пользователь не найден'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'POST'])
@permission_classes([IsAuthenticated])
def simple_animal_update(request, animal_id):
    """Обновление животного - ПРОСТОЙ"""
    if not HAS_MODELS:
        return Response({
            'success': False,
            'error': 'Модели не доступны'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        # Находим кастомного пользователя
        custom_user = User.objects.get(login=request.user.username)

        # Получаем животное (только свое!)
        animal = get_object_or_404(Animal, animal_id=animal_id, user=custom_user)

        # Обновляем поля
        if 'name' in request.data:
            new_name = request.data['name'].strip()
            if len(new_name) < 2:
                return Response({
                    'success': False,
                    'error': 'Имя должно содержать минимум 2 символа'
                }, status=status.HTTP_400_BAD_REQUEST)
            animal.name = new_name

        if 'sex' in request.data:
            animal.sex = request.data['sex']

        if 'age' in request.data:
            animal.age = request.data['age']

        if 'estimated_weight' in request.data:
            animal.estimated_weight = request.data['estimated_weight']

        animal.save()

        return Response({
            'success': True,
            'message': 'Животное обновлено',
            'animal_id': animal.animal_id,
            'name': animal.name
        })

    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Пользователь не найден'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Ошибка при обновлении: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def simple_animal_delete(request, animal_id):
    """Удаление животного - ПРОСТОЙ"""
    if not HAS_MODELS:
        return Response({
            'success': False,
            'error': 'Модели не доступны'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        # Находим кастомного пользователя
        custom_user = User.objects.get(login=request.user.username)

        # Получаем животное (только свое!)
        animal = get_object_or_404(Animal, animal_id=animal_id, user=custom_user)

        # Проверяем, есть ли связанные видео
        has_videos = Video.objects.filter(animal=animal).exists()
        if has_videos:
            return Response({
                'success': False,
                'error': 'Нельзя удалить животное с видео. Сначала удалите видео.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Удаляем
        animal.delete()

        return Response({
            'success': True,
            'message': 'Животное удалено',
            'deleted_id': animal_id
        })

    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Пользователь не найден'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Ошибка при удалении: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def animal_stats(request, animal_id):
    """Статистика по животному (без Ration)"""
    if not HAS_MODELS:
        return Response({
            'success': False,
            'error': 'Модели не доступны'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        custom_user = User.objects.get(login=request.user.username)
        animal = get_object_or_404(Animal, animal_id=animal_id, user=custom_user)

        video_count = Video.objects.filter(animal=animal).count()
        analysis_count = Analysis.objects.filter(video__animal=animal).count()

        # Последний анализ
        last_analysis = Analysis.objects.filter(video__animal=animal).order_by('-analysis_date').first()

        return Response({
            'success': True,
            'stats': {
                'video_count': video_count,
                'analysis_count': analysis_count,
                'last_analysis_date': last_analysis.analysis_date.isoformat() if last_analysis and last_analysis.analysis_date else None,
                'last_lameness_status': last_analysis.is_lame if last_analysis else None
            }
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
