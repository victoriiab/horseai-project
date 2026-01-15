from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from web.database.models import Animal, User
from django.utils import timezone
import json
from django.views.decorators.csrf import csrf_exempt
# ========== VIEW ФУНКЦИИ ==========

def index_view(request):
    """Главная страница"""
    from web.database.models import Animal, Video, Analysis, Ration
    
    context = {
        'user': request.user,
        'animals_count': Animal.objects.count(),
        'videos_count': Video.objects.count(),
        'analyses_count': Analysis.objects.count(),
        'rations_count': Ration.objects.count(),
    }
    
    return render(request, 'frontend/index.html', context)

def login_view(request):
    """Обработка входа пользователя"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Проверяем аутентификацию
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
        login(request, user)
                messages.success(request, f'Добро пожаловать, {user.username}!')
                
                # ПРОВЕРЯЕМ РОЛЬ ПОЛЬЗОВАТЕЛЯ
                try:
                    # Пробуем найти в кастомной таблице
                    from web.database.models import User as CustomUser
                    custom_user = CustomUser.objects.get(login=username)
                    
                    if custom_user.role_id in ['admin', 'superadmin'] or user.is_staff:
                        # Админ - на dashboard
                        return redirect('dashboard')
                    else:
                        # Обычный пользователь - на главную
                        return redirect('index')
                        
                except CustomUser.DoesNotExist:
                    # Если нет в кастомной таблице, проверяем Django
                    if user.is_staff:
                        return redirect('dashboard')
                    else:
                        return redirect('index')
            else:
                messages.error(request, 'Аккаунт неактивен')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    
    # GET запрос или неудачный POST
    return render(request, 'frontend/login.html')

def logout_view(request):
    """Выход из системы с сообщением"""
    from django.contrib.auth import logout
    from django.shortcuts import redirect
    from django.contrib import messages
    
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Вы успешно вышли из системы. До свидания, {username}!')
    else:
        messages.info(request, 'Вы уже вышли из системы')
    
    return redirect('index')

@login_required(login_url='/login/')
def dashboard_view(request):
    """Панель управления с проверкой прав"""
    # ПРОВЕРЯЕМ, ЧТО ПОЛЬЗОВАТЕЛЬ АДМИН
    try:
        from web.database.models import User as CustomUser
        custom_user = CustomUser.objects.get(login=request.user.username)
        
        if not (custom_user.role_id in ['admin', 'superadmin'] or request.user.is_staff):
            messages.error(request, 'У вас нет доступа к панели управления')
            return redirect('index')
            
    except CustomUser.DoesNotExist:
        if not request.user.is_staff:
            messages.error(request, 'У вас нет доступа к панели управления')
            return redirect('index')
    
    # Код dashboard (остается без изменений)
    from django.contrib.auth.models import User
    from web.database.models import Animal, Analysis, Video, Ration
    from django.shortcuts import render
    
    try:
        # Для Animal используем animal_id если нет поля даты
        latest_animals = Animal.objects.order_by('-animal_id')[:5]
    except:
        latest_animals = Animal.objects.all()[:5]

    try:
        # Для Analysis используем analysis_date если есть, иначе analysis_id
        try:
            latest_analyses = Analysis.objects.order_by('-analysis_date')[:5]
        except:
            latest_analyses = Analysis.objects.order_by('-analysis_id')[:5]
    except:
        latest_analyses = []

    context = {
        'user': request.user,
        'users_count': User.objects.count(),
        'animals_count': Animal.objects.count(),
        'videos_count': Video.objects.count(),
        'analyses_count': Analysis.objects.count(),
        'rations_count': Ration.objects.count(),
        'latest_animals': latest_animals,
        'latest_analyses': latest_analyses,
    }

    return render(request, 'frontend/admin_dashboard.html', context)


def animals_view(request):
    """Страница животных"""
    from web.database.models import Animal, User
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        # Получаем пользователя из кастомной таблицы
        custom_user = User.objects.get(login=request.user.username)
        animals = Animal.objects.filter(user=custom_user)
        
        context = {
            'animals': animals,
            'user': request.user
        }
        
        return render(request, 'frontend/animals.html', context)
        
    except User.DoesNotExist:
        # Если пользователь не найден в кастомной таблице
        context = {
            'animals': [],
            'user': request.user,
            'error': 'Пользователь не найден в системе'
        }
        return render(request, 'frontend/animals.html', context)
        
    except Exception as e:
        print(f"Ошибка в animals_view: {e}")
        context = {
            'animals': [],
            'user': request.user,
            'error': str(e)
        }
        return render(request, 'frontend/animals.html', context)

def ration_view(request):
    """Рацион"""
    return render(request, 'frontend/ration.html')

def video_upload_view(request):
    """Загрузка видео"""
    return render(request, 'frontend/video_upload.html')

def video_upload_ml_view(request):
    """ML анализ видео"""
    return render(request, 'frontend/video_upload_real.html')

def analysis_view(request):
    """Результаты анализа"""
    return render(request, 'frontend/analysis.html')

def lameness_test_view(request):
    """Тестовая страница хромоты"""
    return render(request, 'lameness_test.html', {
        'title': 'Тест хромоты',
        'test_result': None
    })

def lameness_test_api(request):
    """API для теста хромоты"""
    return JsonResponse({
        'lameness_probability': 3.25,
        'analysis_complete': True,
        'confidence': 0.89,
        'message': 'Тестовые данные'
    })

def system_stats_api(request):
    """API для получения статистики системы"""
    from web.database.models import Animal, Video, Analysis, Ration
    
    stats = {
        'animals': Animal.objects.count(),
        'videos': Video.objects.count(),
        'analyses': Analysis.objects.count(),
        'rations': Ration.objects.count(),
        'status': 'ok'
    }
    
    return JsonResponse(stats)
# ========== API ДЛЯ ЖИВОТНЫХ ==========

@csrf_exempt
@login_required
def api_add_animal(request):
    """Добавить животное через API"""
    if request.method == 'POST':
        try:
            # Получаем данные
            data = json.loads(request.body)
            print(f"📝 Получены данные для добавления животного: {data}")
            
            # Получаем пользователя из кастомной таблицы
            custom_user = User.objects.get(login=request.user.username)
            print(f"👤 Найден пользователь: {custom_user.login}")
            
            # Парсим данные
            name = data.get('name', 'Без имени')
            sex = data.get('sex', '')
            
            # Берем только первую букву и делаем заглавной
            if sex:
                sex = str(sex)[0].upper()  # "female" → "F", "m" → "M"
            
            # Ограничиваем 1 символом
            sex = sex[:1] if sex else ''
            
            age = data.get('age')
            weight = data.get('weight')
            
            # Конвертируем типы
            if age is not None:
                try:
                    age = int(age)
                except (ValueError, TypeError):
                    age = None
            
            if weight is not None:
                try:
                    weight = float(weight)
                except (ValueError, TypeError):
                    weight = None
            
            print(f"🔧 Обработанные данные: name='{name}', sex='{sex}', age={age}, weight={weight}")
            
            # Создаем животное
            animal = Animal.objects.create(
                user=custom_user,
                name=name,
                sex=sex,
                age=age,
                estimated_weight=weight,
                created_at=timezone.now()
            )
            
            print(f"✅ Животное создано: ID={animal.animal_id}, имя='{animal.name}', пол='{animal.sex}'")
            
            return JsonResponse({
                'success': True,
                'animal_id': animal.animal_id,
                'message': 'Лошадь успешно добавлена!'
            })
            
        except User.DoesNotExist:
            print(f"❌ Пользователь не найден: {request.user.username}")
            return JsonResponse({
                'success': False,
                'error': 'Пользователь не найден'
            }, status=404)
            
        except Exception as e:
            print(f"❌ Ошибка добавления животного: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Используйте POST запрос'
    }, status=400)

@csrf_exempt
@login_required
def api_get_animal(request, animal_id):
    """Получить животное"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
        
        return JsonResponse({
            'animal_id': animal.animal_id,
            'name': animal.name,
            'sex': animal.sex,
            'age': animal.age,
            'estimated_weight': animal.estimated_weight,
            'created_at': animal.created_at.strftime('%Y-%m-%d') if animal.created_at else ''
        })
        
    except (Animal.DoesNotExist, User.DoesNotExist):
        return JsonResponse({
            'success': False,
            'error': 'Животное не найдено'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@login_required
def api_get_user_animals(request):
    """Получить всех животных пользователя"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        animals = Animal.objects.filter(user=custom_user)
        
        animals_list = []
        for animal in animals:
            # Преобразуем одну букву в читаемый вид
            sex_display = {
                'M': '♂️ Жеребец',
                'F': '♀️ Кобыла',
                'G': '🐴 Мерин',
                'm': '♂️ Жеребец',
                'f': '♀️ Кобыла',
                'g': '🐴 Мерин'
            }.get(animal.sex, animal.sex or 'Не указан')
            
            animals_list.append({
                'animal_id': animal.animal_id,
                'name': animal.name,
                'sex': animal.sex,
                'sex_display': sex_display,
                'age': animal.age,
                'estimated_weight': animal.estimated_weight,
                'created_at': animal.created_at.strftime('%Y-%m-%d %H:%M') if animal.created_at else ''
            })
        
        return JsonResponse({
            'success': True,
            'animals': animals_list,
            'count': len(animals_list)
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Пользователь не найден'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
@csrf_exempt
@login_required
def api_update_animal(request, animal_id):
    """Обновить животное"""
    if request.method == 'PUT':
        try:
            # Получаем данные
            data = json.loads(request.body)
            print(f"📝 Получены данные для обновления животного {animal_id}: {data}")
            
            # Получаем пользователя и животное
            custom_user = User.objects.get(login=request.user.username)
            animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
            
            # Обновляем поля
            if 'name' in data:
                animal.name = data['name']
            
            if 'sex' in data:
                sex = data['sex']
                if sex:
                    sex = str(sex)[0].upper()  # Берем первую букву
                    sex = sex[:1] if sex else ''
                animal.sex = sex
            
            if 'age' in data:
                try:
                    animal.age = int(data['age']) if data['age'] is not None else None
                except (ValueError, TypeError):
                    animal.age = None
            
            if 'weight' in data:
                try:
                    animal.estimated_weight = float(data['weight']) if data['weight'] is not None else None
                except (ValueError, TypeError):
                    animal.estimated_weight = None
            
            animal.save()
            
            print(f"✅ Животное обновлено: ID={animal.animal_id}, имя='{animal.name}'")
            
            return JsonResponse({
                'success': True,
                'message': 'Лошадь успешно обновлена!'
            })
            
        except (Animal.DoesNotExist, User.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Животное не найдено'
            }, status=404)
            
        except Exception as e:
            print(f"❌ Ошибка обновления животного: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Используйте PUT запрос'
    }, status=400)

@csrf_exempt
@login_required
def api_delete_animal(request, animal_id):
    """Удалить животное"""
    if request.method == 'DELETE':
        try:
            # Получаем пользователя и животное
            custom_user = User.objects.get(login=request.user.username)
            animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
            
            # Проверяем, есть ли связанные видео
            from web.database.models import Video
            video_count = Video.objects.filter(animal=animal).count()
            
            if video_count > 0:
                return JsonResponse({
                    'success': False,
                    'error': f'Нельзя удалить лошадь. У неё есть {video_count} видео.'
                }, status=400)
            
            # Удаляем животное
            animal_name = animal.name
            animal.delete()
            
            print(f"🗑️ Животное удалено: ID={animal_id}, имя='{animal_name}'")
            
            return JsonResponse({
                'success': True,
                'message': f'Лошадь "{animal_name}" удалена'
            })
            
        except (Animal.DoesNotExist, User.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Животное не найдено'
            }, status=404)
            
        except Exception as e:
            print(f"❌ Ошибка удаления животного: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Используйте DELETE запрос'
    }, status=400)

@csrf_exempt
@login_required
def api_update_animal(request, animal_id):
    """Обновить животное"""
    if request.method == 'PUT':
        try:
            # Получаем данные
            data = json.loads(request.body)
            print(f"📝 Получены данные для обновления животного {animal_id}: {data}")
            
            # Получаем пользователя и животное
            custom_user = User.objects.get(login=request.user.username)
            animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
            
            # Обновляем поля
            if 'name' in data:
                animal.name = data['name']
            
            if 'sex' in data:
                sex = data['sex']
                if sex:
                    sex = str(sex)[0].upper()  # Берем первую букву
                    sex = sex[:1] if sex else ''
                animal.sex = sex
            
            if 'age' in data:
                try:
                    animal.age = int(data['age']) if data['age'] is not None else None
                except (ValueError, TypeError):
                    animal.age = None
            
            if 'weight' in data:
                try:
                    animal.estimated_weight = float(data['weight']) if data['weight'] is not None else None
                except (ValueError, TypeError):
                    animal.estimated_weight = None
            
            animal.save()
            
            print(f"✅ Животное обновлено: ID={animal.animal_id}, имя='{animal.name}'")
            
            return JsonResponse({
                'success': True,
                'message': 'Лошадь успешно обновлена!'
            })
            
        except (Animal.DoesNotExist, User.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Животное не найдено'
            }, status=404)
            
        except Exception as e:
            print(f"❌ Ошибка обновления животного: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Используйте PUT запрос'
    }, status=400)

@csrf_exempt
@login_required
def api_delete_animal(request, animal_id):
    """Удалить животное"""
    if request.method == 'DELETE':
        try:
            # Получаем пользователя и животное
            custom_user = User.objects.get(login=request.user.username)
            animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
            
            # Проверяем, есть ли связанные видео
            from web.database.models import Video
            video_count = Video.objects.filter(animal=animal).count()
            
            if video_count > 0:
                return JsonResponse({
                    'success': False,
                    'error': f'Нельзя удалить лошадь. У неё есть {video_count} видео.'
                }, status=400)
            
            # Удаляем животное
            animal_name = animal.name
            animal.delete()
            
            print(f"🗑️ Животное удалено: ID={animal_id}, имя='{animal_name}'")
            
            return JsonResponse({
                'success': True,
                'message': f'Лошадь "{animal_name}" удалена'
            })
            
        except (Animal.DoesNotExist, User.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Животное не найдено'
            }, status=404)
            
        except Exception as e:
            print(f"❌ Ошибка удаления животного: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Используйте DELETE запрос'
    }, status=400)
# ========== URL PATTERNS ==========

urlpatterns = [
    path('admin/', admin.site.urls),

    # Основные страницы
    path('', index_view, name='index'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('animals/', animals_view, name='animals'),
    path('ration/', ration_view, name='ration'),
    path('video-upload/', video_upload_view, name='video_upload'),
    path('video-upload/ml/', video_upload_ml_view, name='video_upload_ml'),
    path('analysis/results/', analysis_view, name='analysis_results'),

    # Тест хромоты
    path('lameness-test/', lameness_test_view, name='lameness_test_page'),
    path('api/lameness/test/', lameness_test_api, name='lameness_test'),

    # API endpoints - СИСТЕМА
    path('api/system-stats/', system_stats_api, name='system_stats'),
    
    # API endpoints - ЖИВОТНЫЕ
    path('api/animals/add/', api_add_animal, name='api_add_animal'),
    path('api/animals/<int:animal_id>/', api_get_animal, name='api_get_animal'),
    path('api/animals/', api_get_user_animals, name='api_get_user_animals'),
    path('api/animals/<int:animal_id>/update/', api_update_animal, name='api_update_animal'),
    path('api/animals/<int:animal_id>/delete/', api_delete_animal, name='api_delete_animal'),
    
    path('health/', lambda r: JsonResponse({'status': 'healthy'}), name='health'),
]
