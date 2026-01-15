"""
ML Views для обработки видео - фронтенд часть
"""
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.conf import settings

from web.database.models import Animal, User as CustomUser
import requests

@csrf_exempt
@login_required
def upload_video_for_analysis(request):
    """Прокси для загрузки видео в ML API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Получаем CSRF токен
        csrf_token = request.COOKIES.get('csrftoken', '')
        
        # Подготавливаем данные
        data = {
            'animal_id': request.POST.get('animal_id')
        }
        
        files = {}
        if 'video_file' in request.FILES:
            files['video_file'] = request.FILES['video_file']
        
        # Отправляем в основной API
        api_url = f"http://{request.get_host()}/api/ml/upload/"
        
        response = requests.post(
            api_url,
            data=data,
            files=files,
            cookies={'csrftoken': csrf_token, 'sessionid': request.COOKIES.get('sessionid', '')},
            headers={'X-CSRFToken': csrf_token}
        )
        
        return JsonResponse(response.json())
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка при загрузке видео: {str(e)}'
        }, status=500)

@login_required
def get_analysis_status(request, task_id):
    """Прокси для получения статуса анализа"""
    try:
        csrf_token = request.COOKIES.get('csrftoken', '')
        
        api_url = f"http://{request.get_host()}/api/ml/status/{task_id}/"
        
        response = requests.get(
            api_url,
            cookies={'csrftoken': csrf_token, 'sessionid': request.COOKIES.get('sessionid', '')},
            headers={'X-CSRFToken': csrf_token}
        )
        
        return JsonResponse(response.json())
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка получения статуса: {str(e)}'
        }, status=500)

@csrf_exempt
@login_required
def save_analysis_result(request):
    """Прокси для сохранения результата анализа"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        csrf_token = request.COOKIES.get('csrftoken', '')
        
        api_url = f"http://{request.get_host()}/api/ml/save-result/"
        
        response = requests.post(
            api_url,
            json=json.loads(request.body),
            cookies={'csrftoken': csrf_token, 'sessionid': request.COOKIES.get('sessionid', '')},
            headers={'X-CSRFToken': csrf_token}
        )
        
        return JsonResponse(response.json())
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка сохранения результата: {str(e)}'
        }, status=500)

@login_required
def get_video_analysis(request, video_id):
    """Прокси для получения анализа видео"""
    try:
        csrf_token = request.COOKIES.get('csrftoken', '')
        
        api_url = f"http://{request.get_host()}/api/ml/video/{video_id}/analysis/"
        
        response = requests.get(
            api_url,
            cookies={'csrftoken': csrf_token, 'sessionid': request.COOKIES.get('sessionid', '')},
            headers={'X-CSRFToken': csrf_token}
        )
        
        return JsonResponse(response.json())
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка получения анализа: {str(e)}'
        }, status=500)

@login_required
def get_animal_analyses(request, animal_id):
    """Прокси для получения всех анализов животного"""
    try:
        csrf_token = request.COOKILES.get('csrftoken', '')
        
        api_url = f"http://{request.get_host()}/api/ml/animal/{animal_id}/analyses/"
        
        response = requests.get(
            api_url,
            cookies={'csrftoken': csrf_token, 'sessionid': request.COOKIES.get('sessionid', '')},
            headers={'X-CSRFToken': csrf_token}
        )
        
        return JsonResponse(response.json())
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка получения анализов: {str(e)}'
        }, status=500)

# HTML views
@login_required
def video_upload_page(request):
    """Страница загрузки видео"""
    # Получаем животных пользователя
    try:
        custom_user = CustomUser.objects.get(login=request.user.username)
        animals = Animal.objects.filter(user=custom_user).order_by('name')
    except CustomUser.DoesNotExist:
        animals = []
    
    return render(request, 'frontend/video_upload_ml.html', {
        'animals': animals
    })

@login_required
def analysis_results_page(request):
    """Страница результатов анализа"""
    return render(request, 'frontend/analysis_results.html', {})

@login_required
def analysis_detail_page(request, analysis_id):
    """Страница деталей анализа"""
    return render(request, 'frontend/analysis_detail.html', {
        'analysis_id': analysis_id
    })
