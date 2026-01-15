from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def test_api(request):
    """Тестовый API endpoint"""
    return Response({
        'status': 'success',
        'message': 'API работает!',
        'data': {
            'endpoint': '/api/test/',
            'method': 'GET',
            'authenticated': request.user.is_authenticated
        }
    })
