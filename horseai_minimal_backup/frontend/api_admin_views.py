"""
API для админ-панели
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from web.database.models import User, Animal, Video, Analysis
from django.contrib.auth.models import User as AuthUser
from django.db.models import Count, Q
import json

@login_required
@staff_member_required
def admin_users_list(request):
    """Список всех пользователей"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        if not (request.user.is_staff or custom_user.role_id in ['admin', 'superadmin']):
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
    except:
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)

    # Получаем всех пользователей
    users = User.objects.all().order_by('-created_at')
    
    users_list = []
    for user in users:
        users_list.append({
            'user_id': user.user_id,
            'login': user.login,
            'email': user.email,
            'full_name': user.full_name,
            'role_id': user.role_id,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_active': user.is_active,
            'animals_count': Animal.objects.filter(user=user).count(),
            'videos_count': Video.objects.filter(user=user).count()
        })
    
    return JsonResponse({
        'success': True,
        'users': users_list,
        'total': len(users_list)
    })

@login_required
@staff_member_required
def admin_animals_list(request):
    """Список всех животных"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        if not (request.user.is_staff or custom_user.role_id in ['admin', 'superadmin']):
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
    except:
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)

    # Получаем всех животных с владельцами
    animals = Animal.objects.select_related('user').all().order_by('-created_at')
    
    animals_list = []
    for animal in animals:
        animals_list.append({
            'animal_id': animal.animal_id,
            'name': animal.name,
            'sex': animal.sex,
            'age': animal.age,
            'estimated_weight': animal.estimated_weight,
            'created_at': animal.created_at.isoformat() if animal.created_at else None,
            'owner': animal.user.login if animal.user else 'Неизвестно',
            'owner_id': animal.user.user_id if animal.user else None,
            'videos_count': Video.objects.filter(animal=animal).count(),
            'analyses_count': Analysis.objects.filter(video__animal=animal).count()
        })
    
    return JsonResponse({
        'success': True,
        'animals': animals_list,
        'total': len(animals_list)
    })

@login_required
@staff_member_required
def admin_analyses_list(request):
    """Список всех анализов"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        if not (request.user.is_staff or custom_user.role_id in ['admin', 'superadmin']):
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
    except:
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)

    # Получаем все анализы с связанными данными
    analyses = Analysis.objects.select_related(
        'video', 'video__animal', 'video__animal__user'
    ).all().order_by('-analysis_date')
    
    analyses_list = []
    for analysis in analyses:
        analyses_list.append({
            'analysis_id': analysis.analysis_id,
            'video_id': analysis.video.video_id if analysis.video else None,
            'animal_name': analysis.video.animal.name if analysis.video and analysis.video.animal else 'Неизвестно',
            'animal_id': analysis.video.animal.animal_id if analysis.video and analysis.video.animal else None,
            'owner': analysis.video.animal.user.login if analysis.video and analysis.video.animal and analysis.video.animal.user else 'Неизвестно',
            'analysis_date': analysis.analysis_date.isoformat() if analysis.analysis_date else None,
            'is_lame': analysis.is_lame,
            'lameness_probability': analysis.lameness_probability,
            'confidence_score': analysis.confidence_score,
            'diagnosis': analysis.diagnosis,
            'diagnosis_note': analysis.diagnosis_note,
            'posture': analysis.posture,
            'gait_quality': analysis.gait_quality
        })
    
    return JsonResponse({
        'success': True,
        'analyses': analyses_list,
        'total': len(analyses_list)
    })

@csrf_exempt
@login_required
@staff_member_required
def admin_delete_user(request, user_id):
    """Удаление пользователя"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        if not (request.user.is_staff or custom_user.role_id in ['admin', 'superadmin']):
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
    except:
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        user = User.objects.get(user_id=user_id)
        
        # Проверяем, не пытаемся ли удалить себя
        if user.login == request.user.username:
            return JsonResponse({'success': False, 'error': 'Нельзя удалить самого себя'})
        
        # Удаляем связанные Django пользователя (если есть)
        try:
            auth_user = AuthUser.objects.get(username=user.login)
            auth_user.delete()
        except AuthUser.DoesNotExist:
            pass
        
        # Удаляем кастомного пользователя
        user.delete()
        
        return JsonResponse({'success': True, 'message': 'Пользователь удален'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Пользователь не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@staff_member_required
def admin_delete_animal(request, animal_id):
    """Удаление животного"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        if not (request.user.is_staff or custom_user.role_id in ['admin', 'superadmin']):
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
    except:
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        animal = Animal.objects.get(animal_id=animal_id)
        animal.delete()
        return JsonResponse({'success': True, 'message': 'Животное удалено'})
    except Animal.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Животное не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@staff_member_required
def admin_delete_analysis(request, analysis_id):
    """Удаление анализа"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        if not (request.user.is_staff or custom_user.role_id in ['admin', 'superadmin']):
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
    except:
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        analysis = Analysis.objects.get(analysis_id=analysis_id)
        analysis.delete()
        return JsonResponse({'success': True, 'message': 'Анализ удален'})
    except Analysis.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Анализ не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@staff_member_required
def admin_create_user(request):
    """Создание нового пользователя"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST'}, status=405)

    try:
        custom_user = User.objects.get(login=request.user.username)
        if not (request.user.is_staff or custom_user.role_id in ['admin', 'superadmin']):
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
    except:
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        import json
        data = json.loads(request.body)
        
        login = data.get('login')
        email = data.get('email')
        password = data.get('password')
        role_id = data.get('role_id', 'user')
        full_name = data.get('full_name', login)
        
        if not all([login, email, password]):
            return JsonResponse({'success': False, 'error': 'Заполните все поля'})
        
        # Проверяем, нет ли уже такого пользователя
        if User.objects.filter(login=login).exists():
            return JsonResponse({'success': False, 'error': 'Пользователь с таким логином уже существует'})
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': 'Пользователь с таким email уже существует'})
        
        # Создаем Django пользователя
        auth_user = AuthUser.objects.create_user(
            username=login,
            email=email,
            password=password
        )
        
        # Создаем кастомного пользователя
        user = User.objects.create(
            login=login,
            password_hash=password,  # В реальном проекте нужно хэшировать
            email=email,
            full_name=full_name,
            role_id=role_id,
            is_active=True,
            is_staff=role_id in ['admin', 'superadmin'],
            is_superuser=role_id == 'superadmin'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Пользователь создан',
            'user_id': user.user_id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@staff_member_required
def admin_update_user(request, user_id):
    """Обновление пользователя"""
    if request.method != 'PUT':
        return JsonResponse({'success': False, 'error': 'Только PUT'}, status=405)

    try:
        custom_user = User.objects.get(login=request.user.username)
        if not (request.user.is_staff or custom_user.role_id in ['admin', 'superadmin']):
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
    except:
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        import json
        data = json.loads(request.body)
        
        user = User.objects.get(user_id=user_id)
        
        # Обновляем поля
        if 'email' in data:
            user.email = data['email']
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'role_id' in data:
            user.role_id = data['role_id']
            user.is_staff = data['role_id'] in ['admin', 'superadmin']
            user.is_superuser = data['role_id'] == 'superadmin'
        
        user.save()
        
        # Обновляем Django пользователя
        try:
            auth_user = AuthUser.objects.get(username=user.login)
            if 'email' in data:
                auth_user.email = data['email']
            auth_user.save()
        except AuthUser.DoesNotExist:
            pass
        
        return JsonResponse({
            'success': True,
            'message': 'Пользователь обновлен'
        })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Пользователь не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@staff_member_required
def admin_update_analysis(request, analysis_id):
    """Обновление анализа"""
    if request.method != 'PUT':
        return JsonResponse({'success': False, 'error': 'Только PUT'}, status=405)

    try:
        custom_user = User.objects.get(login=request.user.username)
        if not (request.user.is_staff or custom_user.role_id in ['admin', 'superadmin']):
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
    except:
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        import json
        data = json.loads(request.body)
        
        analysis = Analysis.objects.get(analysis_id=analysis_id)
        
        # Обновляем поля
        if 'diagnosis' in data:
            analysis.diagnosis = data['diagnosis']
        if 'diagnosis_note' in data:
            analysis.diagnosis_note = data['diagnosis_note']
        if 'is_lame' in data:
            analysis.is_lame = data['is_lame']
        if 'lameness_probability' in data:
            analysis.lameness_probability = float(data['lameness_probability'])
        if 'confidence_score' in data:
            analysis.confidence_score = float(data['confidence_score'])
        
        analysis.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Анализ обновлен'
        })
        
    except Analysis.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Анализ не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
