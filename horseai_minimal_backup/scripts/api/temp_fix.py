from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from web.database.models import User, Animal
from datetime import datetime

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_animal_fix(request):
    """Временный endpoint для создания животных"""
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
            'animal_id': animal.animal_id,
            'animal_name': animal.name
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
