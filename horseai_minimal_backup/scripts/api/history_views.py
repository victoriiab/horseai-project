from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from web.database.models import Ration, Animal
from web.database.history_models import RationHistory, AnimalHealthHistory
import json

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ration_history(request, ration_id):
    """Получить историю изменений рациона"""
    ration = get_object_or_404(Ration, pk=ration_id)
    
    # Проверка прав доступа
    if request.user.username != ration.animal.user.login:
        return Response({'error': 'Нет доступа'}, status=403)
    
    history = RationHistory.objects.filter(ration=ration).order_by('-change_date')
    
    data = []
    for item in history:
        data.append({
            'history_id': item.history_id,
            'change_date': item.change_date,
            'change_type': item.change_type,
            'change_type_display': item.get_change_type_display(),
            'changed_by': item.changed_by.full_name if item.changed_by else 'Система',
            'previous_composition': item.previous_composition,
            'new_composition': item.new_composition,
            'notes': item.notes,
        })
    
    return Response({
        'success': True,
        'ration_id': ration_id,
        'history': data,
        'total': len(data)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_animal_health_history(request, animal_id):
    """Получить историю здоровья животного"""
    animal = get_object_or_404(Animal, pk=animal_id)
    
    # Проверка прав доступа
    if request.user.username != animal.user.login:
        return Response({'error': 'Нет доступа'}, status=403)
    
    history = AnimalHealthHistory.objects.filter(animal=animal).order_by('-recorded_date')
    
    data = []
    for item in history:
        data.append({
            'history_id': item.history_id,
            'recorded_date': item.recorded_date,
            'lameness_status': item.lameness_status,
            'lameness_status_display': item.get_lameness_status_display(),
            'lameness_probability': item.lameness_probability,
            'confidence_score': item.confidence_score,
            'weight': item.weight,
            'body_condition_score': item.body_condition_score,
            'notes': item.notes,
            'analysis_id': item.analysis.analysis_id if item.analysis else None,
        })
    
    return Response({
        'success': True,
        'animal_id': animal_id,
        'animal_name': animal.name,
        'history': data,
        'total': len(data)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_health_record(request, animal_id):
    """Создать запись в истории здоровья"""
    animal = get_object_or_404(Animal, pk=animal_id)
    
    # Проверка прав доступа
    if request.user.username != animal.user.login:
        return Response({'error': 'Нет доступа'}, status=403)
    
    try:
        custom_user = User.objects.get(login=request.user.username)
        
        record = AnimalHealthHistory.objects.create(
            animal=animal,
            lameness_status=request.data.get('lameness_status', 'healthy'),
            lameness_probability=request.data.get('lameness_probability'),
            confidence_score=request.data.get('confidence_score'),
            weight=request.data.get('weight', animal.estimated_weight),
            body_condition_score=request.data.get('body_condition_score'),
            notes=request.data.get('notes', ''),
        )
        
        return Response({
            'success': True,
            'message': 'Запись создана',
            'record_id': record.history_id
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_ration_history(request, ration_id):
    """Сохранить историю изменения рациона"""
    ration = get_object_or_404(Ration, pk=ration_id)
    
    # Проверка прав доступа
    if request.user.username != ration.animal.user.login:
        return Response({'error': 'Нет доступа'}, status=403)
    
    try:
        custom_user = User.objects.get(login=request.user.username)
        
        history = RationHistory.objects.create(
            ration=ration,
            previous_composition=request.data.get('previous_composition', {}),
            new_composition=request.data.get('new_composition', {}),
            changed_by=custom_user,
            change_type=request.data.get('change_type', 'updated'),
            notes=request.data.get('notes', ''),
        )
        
        return Response({
            'success': True,
            'message': 'История сохранена',
            'history_id': history.history_id
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
