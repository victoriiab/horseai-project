from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

# Ваши функции авторизации
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

# Ваши страницы
@login_required
def index(request):
    return render(request, 'frontend/index.html')

@login_required
def admin_dashboard(request):
    """Дашборд администратора/пользователя"""
    try:
        # Получаем custom пользователя
        from web.database.models import User, Animal, Video, Analysis, Ration
        custom_user = User.objects.get(login=request.user.username)

        # Собираем статистику
        animals_count = Animal.objects.filter(user=custom_user).count()
        videos_count = Video.objects.filter(animal__user=custom_user).count()
        analyses_count = Analysis.objects.filter(video__animal__user=custom_user).count()
        rations_count = Ration.objects.filter(animal__user=custom_user).count()

        # Получаем пользователей (для админа - всех, для обычного - только себя)
        if request.user.is_staff or request.user.is_superuser:
            users_count = User.objects.count()
        else:
            users_count = 1

        context = {
            'users_count': users_count,
            'animals_count': animals_count,
            'videos_count': videos_count,
            'analyses_count': analyses_count,
            'rations_count': rations_count,
            'is_admin': request.user.is_staff or request.user.is_superuser,
        }

        return render(request, 'frontend/admin_dashboard.html', context)

    except User.DoesNotExist:
        # Если пользователь не найден
        context = {
            'users_count': 0,
            'animals_count': 0,
            'videos_count': 0,
            'analyses_count': 0,
            'rations_count': 0,
            'is_admin': False,
        }
        return render(request, 'frontend/admin_dashboard.html', context)

@login_required
def animals_list(request):
    return render(request, 'frontend/animals.html')

@login_required
def ration_calculation(request):
    return render(request, 'frontend/ration.html')

@login_required
def video_upload(request):
    return render(request, 'frontend/video_upload.html')

@login_required
def analysis_results(request):
    return render(request, 'frontend/analysis.html')

# Простые API функции
@csrf_exempt
@login_required
def add_animal_api(request):
    return JsonResponse({'success': True, 'id': 1, 'name': 'Тестовая лошадь'})

@login_required
def get_system_stats(request):
    """Получить статистику системы для текущего пользователя - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        # Импортируем модели
        from web.database.models import User as CustomUser, Animal, Video, Analysis, Ration
        
        # Получаем логин текущего пользователя Django
        auth_username = request.user.username
        
        # Ищем соответствующего кастомного пользователя
        try:
            custom_user = CustomUser.objects.get(login=auth_username)
        except CustomUser.DoesNotExist:
            # Если кастомного пользователя нет, пробуем найти по email
            try:
                custom_user = CustomUser.objects.get(email=request.user.email)
            except (CustomUser.DoesNotExist, AttributeError):
                # Если совсем не нашли, возвращаем нули
                return JsonResponse({
                    'total_animals': 0,
                    'total_videos': 0,
                    'total_analyses': 0,
                    'total_rations': 0,
                    'server_status': 'online',
                    'error': f'Custom user not found for username: {auth_username}'
                })
        
        # Считаем статистику для этого пользователя
        total_animals = Animal.objects.filter(user=custom_user).count()
        
        # Видео: ищем видео, где животное принадлежит пользователю
        total_videos = Video.objects.filter(animal__user=custom_user).count()
        
        # Анализы: ищем анализы видео, где животное принадлежит пользователю
        total_analyses = Analysis.objects.filter(video__animal__user=custom_user).count()
        
        # Рационы: ищем рационы животных, принадлежащих пользователю
        total_rations = Ration.objects.filter(animal__user=custom_user).count()
        
        # Отладочная информация
        print(f"DEBUG get_system_stats:")
        print(f"  User: {custom_user.login} (ID: {custom_user.user_id})")
        print(f"  Animals: {total_animals}")
        print(f"  Videos: {total_videos}")
        print(f"  Analyses: {total_analyses}")
        print(f"  Rations: {total_rations}")
        
        return JsonResponse({
            'total_animals': total_animals,
            'total_videos': total_videos,
            'total_analyses': total_analyses,
            'total_rations': total_rations,
            'server_status': 'online',
            'user': custom_user.login
        })
        
    except Exception as e:
        # В случае ошибки
        import traceback
        error_msg = traceback.format_exc()
        print(f"ERROR in get_system_stats: {error_msg}")
        
        return JsonResponse({
            'total_animals': 0,
            'total_videos': 0,
            'total_analyses': 0,
            'total_rations': 0,
            'server_status': 'online',
            'error': str(e)
        })

# Остальные функции API
@csrf_exempt
@login_required
def upload_video_api(request):
    return JsonResponse({'success': True, 'message': 'Video uploaded'})

@csrf_exempt
@login_required
def upload_video_api_real(request):
    return JsonResponse({'success': True, 'message': 'Real upload'})

@login_required
def get_analysis_status(request, video_id):
    return JsonResponse({'status': 'completed', 'result': {'lameness_score': 0.2}})

@csrf_exempt
@login_required
def create_simple_analysis(request):
    return JsonResponse({'success': True, 'analysis_id': 1})

@csrf_exempt
@login_required
def get_animal_api(request, animal_id):
    return JsonResponse({'success': True, 'animal': {'name': 'Тест', 'age': 5, 'weight': 500}})

@csrf_exempt
@login_required
def update_animal_api(request, animal_id):
    return JsonResponse({'success': True, 'message': 'Updated'})

@csrf_exempt
@login_required
def delete_animal_api(request, animal_id):
    return JsonResponse({'success': True, 'message': 'Deleted'})

@login_required
def upload_video_real_analysis(request):
    return render(request, 'frontend/video_upload.html')
