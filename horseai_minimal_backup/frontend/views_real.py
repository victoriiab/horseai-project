from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
import json

# ========== АВТОРИЗАЦИЯ ==========
def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    return render(request, 'frontend/login.html')

def custom_logout(request):
    logout(request)
    return redirect('login')

# ========== СТРАНИЦЫ ==========
@login_required
def index(request):
    return render(request, 'frontend/index.html')

@login_required
def admin_dashboard(request):
    return render(request, 'frontend/admin_dashboard.html')

@login_required
def animals_list(request):
    """Страница списка животных - загружаем из БД"""
    try:
        from web.database.models import Animal, User
        
        # Находим пользователя в нашей кастомной таблице
        custom_user = User.objects.filter(login=request.user.username).first()
        
        if custom_user:
            # Получаем животных этого пользователя
            animals = Animal.objects.filter(user=custom_user)
            return render(request, 'frontend/animals.html', {'animals': animals})
        else:
            # Если пользователя нет в нашей таблице, показываем пустой список
            return render(request, 'frontend/animals.html', {'animals': []})
            
    except Exception as e:
        print(f"Ошибка загрузки животных: {e}")
        return render(request, 'frontend/animals.html', {'animals': []})

@login_required
def ration_calculation(request):
    return render(request, 'frontend/ration.html')

@login_required
def video_upload(request):
    return render(request, 'frontend/video_upload.html')

@login_required
def analysis_results(request):
    return render(request, 'frontend/analysis.html')

# ========== API СТАТИСТИКИ ==========
@login_required
def get_system_stats(request):
    """Реальная статистика из БД"""
    try:
        from web.database.models import Animal, Video, Analysis, Ration, User
        
        # Находим пользователя
        custom_user = User.objects.filter(login=request.user.username).first()
        
        if custom_user:
            # Статистика только для этого пользователя
            total_animals = Animal.objects.filter(user=custom_user).count()
            total_videos = Video.objects.filter(animal__user=custom_user).count()
            total_analyses = Analysis.objects.filter(video__animal__user=custom_user).count()
            total_rations = Ration.objects.filter(animal__user=custom_user).count()
        else:
            total_animals = total_videos = total_analyses = total_rations = 0
        
        return JsonResponse({
            'total_animals': total_animals,
            'total_videos': total_videos,
            'total_analyses': total_analyses,
            'total_rations': total_rations,
            'server_status': 'online'
        })
        
    except Exception as e:
        print(f"API ошибка: {e}")
        return JsonResponse({
            'total_animals': 0,
            'total_videos': 0,
            'total_analyses': 0,
            'total_rations': 0,
            'server_status': 'error'
        })

# ========== API ЖИВОТНЫХ ==========
@csrf_exempt
@login_required
def api_get_animals(request):
    """Получить список животных из БД"""
    try:
        from web.database.models import Animal, User
        
        # Находим пользователя
        custom_user = User.objects.filter(login=request.user.username).first()
        
        animals = []
        if custom_user:
            # Получаем всех животных пользователя
            for animal in Animal.objects.filter(user=custom_user):
                animals.append({
                    'id': animal.animal_id,
                    'name': animal.name,
                    'age': animal.age,
                    'weight': animal.estimated_weight,
                    'sex': animal.sex,
                    'created_at': animal.created_at.strftime('%d.%m.%Y') if animal.created_at else ''
                })
        
        return JsonResponse({'success': True, 'animals': animals})
        
    except Exception as e:
        print(f"Ошибка загрузки животных (API): {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required
def api_add_animal(request):
    """Добавить животное в БД"""
    if request.method == 'POST':
        try:
            from web.database.models import Animal, User
            
            # Получаем данные
            data = json.loads(request.body) if request.body else request.POST
            
            name = data.get('name', '').strip()
            age = data.get('age', 0)
            weight = data.get('weight', 0)
            sex = data.get('sex', 'не указан')
            
            if not name:
                return JsonResponse({'success': False, 'error': 'Введите имя животного'})
            
            # Находим пользователя
            custom_user = User.objects.filter(login=request.user.username).first()
            if not custom_user:
                return JsonResponse({'success': False, 'error': 'Пользователь не найден'})
            
            # Создаем животное
            animal = Animal.objects.create(
                user=custom_user,
                name=name,
                age=age if age else None,
                estimated_weight=weight if weight else None,
                sex=sex if sex else None,
                created_at=timezone.now()
            )
            
            return JsonResponse({
                'success': True,
                'id': animal.animal_id,
                'name': animal.name,
                'message': f'Животное "{name}" добавлено'
            })
            
        except Exception as e:
            print(f"Ошибка добавления животного: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Неверный метод'})

@csrf_exempt
@login_required
def api_delete_animal(request, animal_id):
    """Удалить животное из БД"""
    try:
        from web.database.models import Animal, User
        
        # Находим пользователя
        custom_user = User.objects.filter(login=request.user.username).first()
        if not custom_user:
            return JsonResponse({'success': False, 'error': 'Пользователь не найден'})
        
        # Находим животное этого пользователя
        animal = Animal.objects.filter(animal_id=animal_id, user=custom_user).first()
        
        if not animal:
            return JsonResponse({'success': False, 'error': 'Животное не найдено'})
        
        # Удаляем
        animal_name = animal.name
        animal.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Животное "{animal_name}" удалено'
        })
        
    except Exception as e:
        print(f"Ошибка удаления животного: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required 
def api_update_animal(request, animal_id):
    """Обновить данные животного"""
    if request.method == 'POST':
        try:
            from web.database.models import Animal, User
            
            data = json.loads(request.body) if request.body else request.POST
            
            # Находим пользователя
            custom_user = User.objects.filter(login=request.user.username).first()
            if not custom_user:
                return JsonResponse({'success': False, 'error': 'Пользователь не найден'})
            
            # Находим животное этого пользователя
            animal = Animal.objects.filter(animal_id=animal_id, user=custom_user).first()
            if not animal:
                return JsonResponse({'success': False, 'error': 'Животное не найдено'})
            
            # Обновляем поля
            if 'name' in data and data['name'].strip():
                animal.name = data['name'].strip()
            if 'age' in data:
                animal.age = data['age'] if data['age'] else None
            if 'weight' in data:
                animal.estimated_weight = data['weight'] if data['weight'] else None
            if 'sex' in data:
                animal.sex = data['sex'] if data['sex'] else None
            
            animal.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Данные обновлены'
            })
            
        except Exception as e:
            print(f"Ошибка обновления животного: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Неверный метод'})

# ========== ЗАГРУЗКА ВИДЕО ==========
@csrf_exempt
@login_required
def api_upload_video(request):
    """Загрузить видео"""
    return JsonResponse({'success': True, 'message': 'В разработке'})

@csrf_exempt
@login_required
def api_analyze_video(request):
    """Анализ видео"""
    return JsonResponse({'success': True, 'message': 'В разработке'})
