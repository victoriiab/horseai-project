"""
API endpoints для супер-администратора - ПОЛНАЯ РАБОЧАЯ ВЕРСИЯ
"""

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from django.db import connection
from django.utils import timezone
from datetime import timedelta
import json
import csv
import os
import psutil
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Импорт моделей из правильного места
from web.database.models import User, Animal, Video, Analysis, Ration
from django.contrib.auth.models import User as AuthUser

# ========== ПРОВЕРКА ПРАВ ==========
def is_super_admin(request):
    """Проверка, является ли пользователь супер-админом"""
    return request.user.is_authenticated and request.user.is_staff

# ========== ОСНОВНАЯ СТАТИСТИКА ==========

@api_view(['GET'])
def super_admin_stats(request):
    """Полная статистика для супер-админа"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        # Общая статистика
        total_users = User.objects.count()
        total_animals = Animal.objects.count()
        total_videos = Video.objects.count()
        total_analyses = Analysis.objects.count()

        # Активные пользователи (за последние 30 дней)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        active_users = User.objects.filter(last_login__gte=thirty_days_ago).count()

        # Видео по статусам
        video_statuses = Video.objects.values('analysis_status').annotate(count=Count('analysis_status'))
        video_status_dict = {status['analysis_status']: status['count'] for status in video_statuses}

        # Анализы по статусу хромоты
        lame_count = Analysis.objects.filter(Q(diagnosis__icontains='хром') | Q(diagnosis__icontains='lame')).count()
        healthy_count = Analysis.objects.filter(diagnosis__icontains='здор').count()

        # Если нет конкретных диагнозов, используем lameness_probability
        if lame_count == 0 and healthy_count == 0:
            lame_count = Analysis.objects.filter(lameness_probability__gte=50).count()
            healthy_count = Analysis.objects.filter(lameness_probability__lt=50).count()

        # Последние 5 пользователей
        recent_users = list(User.objects.order_by('-created_at')[:5].values(
            'user_id', 'login', 'email', 'role_id', 'created_at'
        ))

        # Последние 10 анализов
        recent_analyses = list(Analysis.objects.select_related('video', 'video__animal', 'video__user')
                              .order_by('-analysis_date')[:10].values(
            'analysis_id', 'analysis_date', 'diagnosis', 'diagnosis_note',
            animal_name=F('video__animal__name'),
            owner_login=F('video__user__login')
        ))

        # Статистика по дням (последние 7 дней)
        seven_days_ago = timezone.now() - timedelta(days=7)
        daily_stats = []
        for i in range(7):
            day = seven_days_ago + timedelta(days=i)
            next_day = day + timedelta(days=1)

            day_videos = Video.objects.filter(
                upload_date__gte=day,
                upload_date__lt=next_day
            ).count()

            day_analyses = Analysis.objects.filter(
                analysis_date__gte=day,
                analysis_date__lt=next_day
            ).count()

            daily_stats.append({
                'date': day.strftime('%Y-%m-%d'),
                'videos': day_videos,
                'analyses': day_analyses
            })

        return Response({
            'success': True,
            'total_users': total_users,
            'active_users': active_users,
            'total_animals': total_animals,
            'total_videos': total_videos,
            'video_statuses': video_status_dict,
            'total_analyses': total_analyses,
            'lame_count': lame_count,
            'healthy_count': healthy_count,
            'lame_percentage': round((lame_count / total_analyses * 100), 1) if total_analyses > 0 else 0,
            'recent_users': recent_users,
            'recent_analyses': recent_analyses,
            'daily_stats': daily_stats,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# ========== СИСТЕМНЫЕ ФУНКЦИИ ==========

@api_view(['GET'])
def super_admin_system_health(request):
    """Проверка здоровья системы"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        # Информация о системе
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Информация о Django
        from django.core.cache import cache

        db_status = 'OK'
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as db_error:
            db_status = f'ERROR: {str(db_error)}'

        cache_status = 'OK'
        try:
            cache.set('health_check', 'test', 10)
            if cache.get('health_check') != 'test':
                cache_status = 'WARNING'
        except Exception as cache_error:
            cache_status = f'ERROR: {str(cache_error)}'

        # Проверка медиа папки
        media_path = '/home/ais/shared/horseAI/media'
        media_exists = os.path.exists(media_path)
        media_writable = os.access(media_path, os.W_OK) if media_exists else False

        # Проверка места в БД
        db_size_mb = 0
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT SUM(data_length + index_length) FROM information_schema.TABLES WHERE table_schema = DATABASE()")
                result = cursor.fetchone()
                if result and result[0]:
                    db_size_mb = round(result[0] / (1024 * 1024), 2)
        except Exception as db_size_error:
            db_size_mb = f'ERROR: {str(db_size_error)}'

        return Response({
            'success': True,
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': round(memory.percent, 1),
                'memory_used_mb': round(memory.used / (1024 * 1024)),
                'memory_total_mb': round(memory.total / (1024 * 1024)),
                'disk_percent': disk.percent,
                'disk_free_gb': round(disk.free / (1024 ** 3), 1),
                'disk_total_gb': round(disk.total / (1024 ** 3), 1),
                'uptime_seconds': int(psutil.boot_time())
            },
            'services': {
                'database': db_status,
                'database_size_mb': db_size_mb,
                'cache': cache_status,
                'media_folder': 'OK' if media_exists and media_writable else 'ERROR'
            },
            'app': {
                'total_users': User.objects.count(),
                'total_animals': Animal.objects.count(),
                'total_videos': Video.objects.count(),
                'total_analyses': Analysis.objects.count(),
                'processing_videos': Video.objects.filter(analysis_status='processing').count(),
                'failed_videos': Video.objects.filter(analysis_status='failed').count(),
                'pending_videos': Video.objects.filter(analysis_status='pending').count()
            },
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# ========== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ==========

@api_view(['GET'])
def super_admin_users(request):
    """Получить всех пользователей с пагинацией"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        page = int(request.GET.get('page', 1))
        search = request.GET.get('search', '')
        role = request.GET.get('role', '')

        per_page = 10
        offset = (page - 1) * per_page

        # Базовый запрос
        users = User.objects.all().order_by('-created_at')

        # Применяем фильтры
        if search:
            users = users.filter(
                Q(login__icontains=search) |
                Q(email__icontains=search) |
                Q(full_name__icontains=search)
            )

        if role:
            users = users.filter(role_id=role)

        # Считаем общее количество
        total_count = users.count()
        total_pages = (total_count + per_page - 1) // per_page

        # Применяем пагинацию
        users = users[offset:offset + per_page]

        user_list = []
        for user in users:
            # Проверяем наличие атрибута is_active
            is_active = getattr(user, 'is_active', True)

            user_list.append({
                'user_id': user.user_id,
                'login': user.login,
                'email': user.email,
                'full_name': user.full_name or user.login,
                'role_id': user.role_id or 'user',
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_active': is_active,
                'animals_count': Animal.objects.filter(user=user).count(),
                'videos_count': Video.objects.filter(user=user).count(),
                'analyses_count': Analysis.objects.filter(video__user=user).count()
            })

        return Response({
            'success': True,
            'users': user_list,
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def super_admin_user_detail(request, user_id):
    """Получить детальную информацию о пользователе"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        user = get_object_or_404(User, user_id=user_id)

        # Проверяем наличие атрибута is_active
        is_active = getattr(user, 'is_active', True)

        user_data = {
            'user_id': user.user_id,
            'login': user.login,
            'email': user.email,
            'full_name': user.full_name or user.login,
            'role_id': user.role_id or 'user',
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_active': is_active,
        }

        # Добавляем статистику пользователя
        user_data['animals'] = list(Animal.objects.filter(user=user).values(
            'animal_id', 'name', 'sex', 'age', 'estimated_weight'
        )[:5])

        user_data['videos'] = list(Video.objects.filter(user=user).values(
            'video_id', 'file_path', 'upload_date', 'analysis_status'
        )[:5])

        user_data['analyses'] = list(Analysis.objects.filter(video__user=user).values(
            'analysis_id', 'analysis_date', 'diagnosis'
        )[:5])

        return Response({
            'success': True,
            'user': user_data
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
def super_admin_add_user(request):
    """Добавить нового пользователя"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        full_name = request.data.get('full_name', username)
        role_id = request.data.get('role', 'user')

        if not all([username, password]):
            return Response({
                'success': False,
                'error': 'Заполните обязательные поля (логин, пароль)'
            }, status=400)

        # Проверяем, нет ли уже такого пользователя
        if User.objects.filter(login=username).exists():
            return Response({
                'success': False,
                'error': 'Пользователь с таким логином уже существует'
            }, status=400)

        # Создаем Django пользователя
        from django.contrib.auth.hashers import make_password

        # Создаем кастомного пользователя
        custom_user = User.objects.create(
            login=username,
            password_hash=make_password(password),
            email=email or f"{username}@example.com",
            full_name=full_name,
            role_id=role_id,
            created_at=timezone.now(),
            last_login=timezone.now(),
        )

        # Добавляем is_active если поле существует
        try:
            custom_user.is_active = True
            custom_user.save()
        except:
            pass  # Поле может не существовать

        # Создаем Django auth пользователя
        auth_user = AuthUser.objects.create_user(
            username=username,
            password=password,
            email=email or f"{username}@example.com",
            first_name=full_name,
            is_staff=(role_id in ['admin', 'superadmin']),
            is_superuser=(role_id == 'superadmin')
        )

        return Response({
            'success': True,
            'message': 'Пользователь создан успешно',
            'user_id': custom_user.user_id,
            'auth_user_id': auth_user.id
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
def super_admin_edit_user(request, user_id):
    """Редактировать пользователя"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        user = get_object_or_404(User, user_id=user_id)

        # Обновляем поля
        if 'email' in request.data:
            user.email = request.data['email']

        if 'full_name' in request.data:
            user.full_name = request.data['full_name']

        if 'role_id' in request.data:
            user.role_id = request.data['role_id']

            # Обновляем Django пользователя
            try:
                auth_user = AuthUser.objects.get(username=user.login)
                auth_user.is_staff = (request.data['role_id'] in ['admin', 'superadmin'])
                auth_user.is_superuser = (request.data['role_id'] == 'superadmin')
                auth_user.save()
            except AuthUser.DoesNotExist:
                pass

        # Обновляем is_active если поле существует
        if 'is_active' in request.data:
            try:
                user.is_active = bool(request.data['is_active'])
            except:
                pass  # Поле может не существовать

            # Обновляем Django пользователя
            try:
                auth_user = AuthUser.objects.get(username=user.login)
                auth_user.is_active = bool(request.data['is_active'])
                auth_user.save()
            except AuthUser.DoesNotExist:
                pass

        user.save()

        return Response({
            'success': True,
            'message': 'Пользователь обновлен'
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
def super_admin_toggle_user_status(request, user_id):
    """Включить/выключить пользователя"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        user = get_object_or_404(User, user_id=user_id)

        # Переключаем статус если поле существует
        try:
            current_status = getattr(user, 'is_active', True)
            user.is_active = not current_status
            new_status = user.is_active
        except:
            # Если поля нет, создаем его
            user.is_active = False
            new_status = False

        user.save()

        # Обновляем Django пользователя
        try:
            auth_user = AuthUser.objects.get(username=user.login)
            auth_user.is_active = new_status
            auth_user.save()
        except AuthUser.DoesNotExist:
            pass

        return Response({
            'success': True,
            'message': f'Пользователь {"активирован" if new_status else "деактивирован"}',
            'is_active': new_status
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['DELETE'])
def super_admin_delete_user(request, user_id):
    """Удалить пользователя"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        user = get_object_or_404(User, user_id=user_id)
        login = user.login

        # Удаляем Django пользователя
        try:
            auth_user = AuthUser.objects.get(username=login)
            auth_user.delete()
        except AuthUser.DoesNotExist:
            pass

        # Удаляем кастомного пользователя
        user.delete()

        return Response({
            'success': True,
            'message': 'Пользователь удален'
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# ========== УПРАВЛЕНИЕ ЖИВОТНЫМИ ==========

@api_view(['GET'])
def super_admin_animals(request):
    """Получить всех животных с пагинацией"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        page = int(request.GET.get('page', 1))
        search = request.GET.get('search', '')

        per_page = 10
        offset = (page - 1) * per_page

        # Базовый запрос
        animals = Animal.objects.select_related('user').all().order_by('-created_at')

        # Применяем фильтры
        if search:
            animals = animals.filter(
                Q(name__icontains=search) |
                Q(user__login__icontains=search) |
                Q(user__full_name__icontains=search)
            )

        # Считаем общее количество
        total_count = animals.count()
        total_pages = (total_count + per_page - 1) // per_page

        # Применяем пагинацию
        animals = animals[offset:offset + per_page]

        animal_list = []
        for animal in animals:
            animal_list.append({
                'animal_id': animal.animal_id,
                'name': animal.name,
                'sex': animal.sex,
                'age': animal.age,
                'estimated_weight': animal.estimated_weight,
                'created_at': animal.created_at.isoformat() if animal.created_at else None,
                'owner_name': animal.user.full_name if animal.user else 'Не указан',
                'owner_login': animal.user.login if animal.user else 'Не указан',
                'analyses_count': Analysis.objects.filter(video__animal=animal).count()
            })

        return Response({
            'success': True,
            'animals': animal_list,
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# ========== УПРАВЛЕНИЕ ВИДЕО ==========

@api_view(['GET'])
def super_admin_videos(request):
    """Получить все видео с пагинацией"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        page = int(request.GET.get('page', 1))
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')

        per_page = 10
        offset = (page - 1) * per_page

        # Базовый запрос
        videos = Video.objects.select_related('user', 'animal').all().order_by('-upload_date')

        # Применяем фильтры
        if search:
            videos = videos.filter(
                Q(file_path__icontains=search) |
                Q(animal__name__icontains=search) |
                Q(user__login__icontains=search)
            )

        if status_filter:
            videos = videos.filter(analysis_status=status_filter)

        # Считаем общее количество
        total_count = videos.count()
        total_pages = (total_count + per_page - 1) // per_page

        # Применяем пагинацию
        videos = videos[offset:offset + per_page]

        video_list = []
        for video in videos:
            video_list.append({
                'video_id': video.video_id,
                'file_path': video.file_path,
                'upload_date': video.upload_date.isoformat() if video.upload_date else None,
                'duration': video.duration,
                'resolution': video.resolution,
                'analysis_status': video.analysis_status,
                'animal_name': video.animal.name if video.animal else 'Не указано',
                'owner_login': video.user.login if video.user else 'Не указан',
                'has_analysis': Analysis.objects.filter(video=video).exists()
            })

        return Response({
            'success': True,
            'videos': video_list,
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def super_admin_video_detail(request, video_id):
    """Получить детальную информацию о видео"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        video = get_object_or_404(Video, video_id=video_id)

        video_data = {
            'video_id': video.video_id,
            'file_path': video.file_path,
            'upload_date': video.upload_date.isoformat() if video.upload_date else None,
            'duration': video.duration,
            'resolution': video.resolution,
            'analysis_status': video.analysis_status,
        }

        # Добавляем информацию о животном
        if video.animal:
            video_data['animal'] = {
                'animal_id': video.animal.animal_id,
                'name': video.animal.name,
                'sex': video.animal.sex,
                'age': video.animal.age,
                'estimated_weight': video.animal.estimated_weight
            }

        # Добавляем информацию о владельце
        if video.user:
            video_data['owner'] = {
                'user_id': video.user.user_id,
                'login': video.user.login,
                'email': video.user.email,
                'full_name': video.user.full_name
            }

        # Добавляем информацию об анализе если есть
        analysis = Analysis.objects.filter(video=video).first()
        if analysis:
            video_data['analysis'] = {
                'analysis_id': analysis.analysis_id,
                'analysis_date': analysis.analysis_date.isoformat() if analysis.analysis_date else None,
                'diagnosis': analysis.diagnosis,
                'diagnosis_note': analysis.diagnosis_note,
                'confidence_score': analysis.confidence_score,
                'lameness_probability': analysis.lameness_probability
            }

        return Response({
            'success': True,
            'video': video_data
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['DELETE'])
def super_admin_delete_video(request, video_id):
    """Удалить видео - ИСПРАВЛЕННАЯ ВЕРСИЯ с учетом зависимостей"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        print(f"🔍 Попытка удаления видео ID: {video_id}")

        # Получаем видео
        video = Video.objects.get(video_id=video_id)
        print(f"  Найдено видео: {video.file_path}")

        # Получаем связанные анализы
        analyses = Analysis.objects.filter(video=video)
        analyses_count = analyses.count()
        print(f"  Найдено связанных анализов: {analyses_count}")

        deleted_rations_count = 0
        deleted_analyses_count = 0

        # Для каждого анализа удаляем связанные рационы
        for analysis in analyses:
            # Удаляем связанные рационы
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM database_ration WHERE analysis_id = %s', [analysis.analysis_id])
                rations_deleted = cursor.rowcount
                deleted_rations_count += rations_deleted
                if rations_deleted > 0:
                    print(f"  Удалено рационов для анализа {analysis.analysis_id}: {rations_deleted}")

        # Удаляем анализы
        if analyses_count > 0:
            deleted_count, _ = analyses.delete()
            deleted_analyses_count = deleted_count
            print(f"  Удалено анализов: {deleted_analyses_count}")

        # Удаляем файл если он существует
        file_deleted = False
        file_path_info = None

        if video.file_path:
            # Проверяем разные возможные пути
            possible_paths = [
                os.path.join(settings.MEDIA_ROOT, video.file_path),
                video.file_path,
                os.path.join('/home/ais/shared/horseAI/media', video.file_path),
                os.path.join('/home/ais/shared/horseAI/media/videos', video.file_path.split('/')[-1] if '/' in video.file_path else video.file_path),
                os.path.join('/home/ais/shared/horseAI/media/videos/', video.file_path)
            ]

            for file_path in possible_paths:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"  ✅ Удален файл: {file_path}")
                        file_deleted = True
                        file_path_info = file_path
                        break
                    except Exception as e:
                        print(f"  ⚠️  Ошибка удаления файла {file_path}: {e}")
                        continue

        # Удаляем видео из БД
        video.delete()
        print(f"  ✅ Видео удалено из БД")

        return Response({
            'success': True,
            'message': f'Видео удалено успешно',
            'video_id': video_id,
            'deleted_rations': deleted_rations_count,
            'deleted_analyses': deleted_analyses_count,
            'file_deleted': file_deleted,
            'file_path': file_path_info
        })

    except Video.DoesNotExist:
        print(f"  ❌ Видео с ID {video_id} не найдено")
        return Response({
            'success': False,
            'error': f'Видео с ID {video_id} не найдено'
        }, status=404)
    except Exception as e:
        print(f"  ❌ Критическая ошибка при удалении видео {video_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        }, status=500)

# ========== УПРАВЛЕНИЕ АНАЛИЗАМИ ==========

@api_view(['GET'])
def super_admin_analyses(request):
    """Получить все анализы с пагинацией"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        page = int(request.GET.get('page', 1))
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        lameness_filter = request.GET.get('lameness', '')

        per_page = 10
        offset = (page - 1) * per_page

        # Базовый запрос
        analyses = Analysis.objects.select_related(
            'video', 'video__animal', 'video__user'
        ).order_by('-analysis_date')

        # Применяем фильтры
        if search:
            analyses = analyses.filter(
                Q(diagnosis__icontains=search) |
                Q(diagnosis_note__icontains=search) |
                Q(video__animal__name__icontains=search) |
                Q(video__user__login__icontains=search)
            )

        if status_filter:
            analyses = analyses.filter(video__analysis_status=status_filter)

        if lameness_filter == 'true':
            analyses = analyses.filter(Q(diagnosis__icontains='хром') | Q(diagnosis__icontains='lame'))
        elif lameness_filter == 'false':
            analyses = analyses.exclude(Q(diagnosis__icontains='хром') | Q(diagnosis__icontains='lame'))

        # Считаем общее количество
        total_count = analyses.count()
        total_pages = (total_count + per_page - 1) // per_page

        # Применяем пагинацию
        analyses = analyses[offset:offset + per_page]

        analysis_list = []
        for analysis in analyses:
            analysis_list.append({
                'analysis_id': analysis.analysis_id,
                'analysis_date': analysis.analysis_date.isoformat() if analysis.analysis_date else None,
                'diagnosis': analysis.diagnosis,
                'diagnosis_note': analysis.diagnosis_note,
                'posture': analysis.posture,
                'gait_quality': analysis.gait_quality,
                'size_category': analysis.size_category,
                'estimated_weight': analysis.estimated_weight,
                'confidence_score': analysis.confidence_score,
                'lameness_probability': analysis.lameness_probability,
                'lameness_confidence': analysis.lameness_confidence,
                'animal_name': analysis.video.animal.name if analysis.video and analysis.video.animal else 'Не указано',
                'owner_name': analysis.video.user.full_name if analysis.video and analysis.video.user else 'Не указан',
                'owner_login': analysis.video.user.login if analysis.video and analysis.video.user else 'Не указан',
                'video_status': analysis.video.analysis_status if analysis.video else 'Не указан'
            })

        return Response({
            'success': True,
            'analyses': analysis_list,
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def super_admin_analysis_detail(request, analysis_id):
    """Получить детали анализа"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        analysis = get_object_or_404(Analysis, analysis_id=analysis_id)

        data = {
            'analysis_id': analysis.analysis_id,
            'analysis_date': analysis.analysis_date.isoformat() if analysis.analysis_date else None,
            'posture': analysis.posture,
            'gait_quality': analysis.gait_quality,
            'size_category': analysis.size_category,
            'estimated_weight': analysis.estimated_weight,
            'confidence_score': analysis.confidence_score,
            'lameness_probability': analysis.lameness_probability,
            'lameness_confidence': analysis.lameness_confidence,
            'diagnosis': analysis.diagnosis,
            'diagnosis_note': analysis.diagnosis_note
        }

        # Добавляем информацию о видео и животном
        if analysis.video:
            data['video'] = {
                'video_id': analysis.video.video_id,
                'file_path': analysis.video.file_path,
                'upload_date': analysis.video.upload_date.isoformat() if analysis.video.upload_date else None,
                'duration': analysis.video.duration,
                'resolution': analysis.video.resolution,
                'analysis_status': analysis.video.analysis_status
            }

            if analysis.video.animal:
                data['animal'] = {
                    'animal_id': analysis.video.animal.animal_id,
                    'name': analysis.video.animal.name,
                    'sex': analysis.video.animal.sex,
                    'age': analysis.video.animal.age,
                    'estimated_weight': analysis.video.animal.estimated_weight
                }

            if analysis.video.user:
                data['owner'] = {
                    'user_id': analysis.video.user.user_id,
                    'login': analysis.video.user.login,
                    'email': analysis.video.user.email,
                    'full_name': analysis.video.user.full_name
                }

        return Response({
            'success': True,
            'analysis': data
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
def super_admin_update_analysis(request, analysis_id):
    """Обновить анализ"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        analysis = get_object_or_404(Analysis, analysis_id=analysis_id)

        # Обновляем доступные поля
        update_fields = [
            'diagnosis', 'diagnosis_note', 'posture', 'gait_quality',
            'size_category', 'estimated_weight', 'confidence_score',
            'lameness_probability', 'lameness_confidence'
        ]

        for field in update_fields:
            if field in request.data:
                setattr(analysis, field, request.data[field])

        analysis.save()

        return Response({
            'success': True,
            'message': 'Анализ обновлен'
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['DELETE'])
def super_admin_delete_analysis(request, analysis_id):
    """Удалить анализ"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        analysis = get_object_or_404(Analysis, analysis_id=analysis_id)

        # Удаляем связанные рационы
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM database_ration WHERE analysis_id = %s', [analysis_id])

        # Удаляем анализ
        analysis.delete()

        return Response({
            'success': True,
            'message': 'Анализ удален успешно'
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# ========== ЭКСПОРТ ДАННЫХ ==========

@api_view(['POST'])
def super_admin_export_data(request):
    """Экспорт данных в CSV"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        data_type = request.data.get('type', 'analyses')

        if data_type == 'analyses':
            analyses = Analysis.objects.select_related('video', 'video__animal', 'video__user').all()

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="analyses_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

            writer = csv.writer(response)
            writer.writerow(['ID', 'Дата', 'Животное', 'Владелец', 'Диагноз', 'Хромота', 'Вероятность', 'Уверенность', 'Примечание'])

            for analysis in analyses:
                writer.writerow([
                    analysis.analysis_id,
                    analysis.analysis_date.strftime('%Y-%m-%d %H:%M:%S') if analysis.analysis_date else '',
                    analysis.video.animal.name if analysis.video and analysis.video.animal else '',
                    analysis.video.user.full_name if analysis.video and analysis.video.user else '',
                    analysis.diagnosis or '',
                    'ДА' if 'хром' in (analysis.diagnosis or '').lower() or (analysis.lameness_probability or 0) > 50 else 'НЕТ',
                    f"{analysis.lameness_probability}%" if analysis.lameness_probability else '0%',
                    f"{analysis.confidence_score * 100}%" if analysis.confidence_score else '0%',
                    analysis.diagnosis_note or ''
                ])

            return response

        elif data_type == 'users':
            users = User.objects.all()

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="users_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

            writer = csv.writer(response)
            writer.writerow(['ID', 'Логин', 'Email', 'Имя', 'Роль', 'Дата регистрации', 'Последний вход', 'Активен', 'Животных', 'Видео', 'Анализов'])

            for user in users:
                writer.writerow([
                    user.user_id,
                    user.login,
                    user.email or '',
                    user.full_name or '',
                    user.role_id or 'user',
                    user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                    user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                    'ДА' if getattr(user, 'is_active', True) else 'НЕТ',
                    Animal.objects.filter(user=user).count(),
                    Video.objects.filter(user=user).count(),
                    Analysis.objects.filter(video__user=user).count()
                ])

            return response

        else:
            return Response({
                'success': False,
                'error': f'Неподдерживаемый тип данных: {data_type}. Доступные: analyses, users'
            }, status=400)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


# ========== ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ЖИВОТНЫХ ==========

@api_view(['GET'])
def super_admin_animal_detail(request, animal_id):
    """Получить детальную информацию о животном"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        animal = get_object_or_404(Animal, animal_id=animal_id)

        # Получаем статистику
        videos_count = Video.objects.filter(animal=animal).count()
        analyses_count = Analysis.objects.filter(video__animal=animal).count()
        rations_count = Ration.objects.filter(animal=animal).count()

        # Последние 5 видео
        recent_videos = Video.objects.filter(animal=animal).order_by('-upload_date')[:5]

        animal_data = {
            'animal_id': animal.animal_id,
            'name': animal.name,
            'sex': animal.sex,
            'age': animal.age,
            'estimated_weight': animal.estimated_weight,
            'created_at': animal.created_at.isoformat() if animal.created_at else None,
            'videos_count': videos_count,
            'analyses_count': analyses_count,
            'rations_count': rations_count,
        }

        # Добавляем информацию о владельце
        if animal.user:
            animal_data['owner'] = {
                'user_id': animal.user.user_id,
                'login': animal.user.login,
                'email': animal.user.email,
                'full_name': animal.user.full_name,
            }

        # Добавляем информацию о видео
        animal_data['videos'] = [
            {
                'video_id': video.video_id,
                'file_path': video.file_path,
                'upload_date': video.upload_date.isoformat() if video.upload_date else None,
                'analysis_status': video.analysis_status,
            }
            for video in recent_videos
        ]

        return Response({
            'success': True,
            'animal': animal_data
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
def super_admin_edit_animal(request, animal_id):
    """Редактировать животное"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        animal = get_object_or_404(Animal, animal_id=animal_id)

        # Обновляем поля
        if 'name' in request.data:
            animal.name = request.data['name']
        if 'sex' in request.data and request.data['sex'] in ['M', 'F', '']:
            animal.sex = request.data['sex'] if request.data['sex'] else None
        if 'age' in request.data:
            try:
                animal.age = float(request.data['age']) if request.data['age'] not in [None, ''] else None
            except:
                pass
        if 'estimated_weight' in request.data:
            try:
                animal.estimated_weight = float(request.data['estimated_weight']) if request.data['estimated_weight'] not in [None, ''] else None
            except:
                pass

        animal.save()

        return Response({
            'success': True,
            'message': 'Животное успешно обновлено',
            'animal': {
                'animal_id': animal.animal_id,
                'name': animal.name,
                'sex': animal.sex,
                'age': animal.age,
                'estimated_weight': animal.estimated_weight,
            }
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['DELETE'])
def super_admin_delete_animal(request, animal_id):
    """Удалить животное"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        animal = get_object_or_404(Animal, animal_id=animal_id)

        # Удаляем животное
        animal.delete()

        return Response({
            'success': True,
            'message': 'Животное успешно удалено'
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# ========== УПРАВЛЕНИЕ РАЦИОНАМИ ==========

@api_view(['GET'])
def super_admin_rations(request):
    """Получить все рационы с пагинацией"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        print(f"🔍 Получение рационов. Пользователь: {request.user}")
        
        page = int(request.GET.get('page', 1))
        search = request.GET.get('search', '')
        print(f"  Параметры: page={page}, search='{search}'")

        per_page = 10
        offset = (page - 1) * per_page

        # Базовый запрос - используем calculation_date вместо created_at
        print("  Создаю базовый запрос...")
        rations = Ration.objects.select_related(
            'analysis', 
            'analysis__video', 
            'analysis__video__animal', 
            'analysis__video__user'
        ).all().order_by('-calculation_date')  # Изменено с created_at на calculation_date
        
        print(f"  Найдено рационов: {rations.count()}")

        # Применяем фильтры
        if search:
            print(f"  Применяю фильтр поиска: '{search}'")
            rations = rations.filter(
                Q(composition__icontains=search) |
                Q(analysis__video__animal__name__icontains=search) |
                Q(analysis__video__user__login__icontains=search)
            )

        # Считаем общее количество
        total_count = rations.count()
        total_pages = (total_count + per_page - 1) // per_page
        print(f"  Всего рационов: {total_count}, страниц: {total_pages}")

        # Применяем пагинацию
        rations = rations[offset:offset + per_page]
        print(f"  Рационов после пагинации: {rations.count()}")

        ration_list = []
        for i, ration in enumerate(rations):
            print(f"  Обработка рациона {i+1}: ID={ration.ration_id}")
            
            try:
                animal_name = 'Не указано'
                owner_login = 'Не указан'
                analysis_id = None
                animal_id = None
                
                if ration.animal:
                    animal_name = ration.animal.name
                    animal_id = ration.animal.animal_id
                elif ration.analysis and ration.analysis.video and ration.analysis.video.animal:
                    animal_name = ration.analysis.video.animal.name
                    animal_id = ration.analysis.video.animal.animal_id
                
                if ration.analysis:
                    analysis_id = ration.analysis.analysis_id
                    if ration.analysis.video and ration.analysis.video.user:
                        owner_login = ration.analysis.video.user.login
                
                ration_list.append({
                    'ration_id': ration.ration_id,
                    'animal_name': animal_name,
                    'animal_id': animal_id,
                    'calculation_date': ration.calculation_date.isoformat() if ration.calculation_date else None,
                    'composition': ration.composition or 'Без описания',
                    'energy_content': ration.energy_content,
                    'total_dmi': ration.total_dmi,
                    'analysis_id': analysis_id,
                    'owner_login': owner_login
                })
                print(f"    Добавлен рацион: {ration.ration_id}")
            except Exception as e:
                print(f"    ⚠️ Ошибка обработки рациона {ration.ration_id}: {str(e)}")
                continue

        print(f"✅ Успешно обработано {len(ration_list)} рационов")

        return Response({
            'success': True,
            'rations': ration_list,
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages
        })

    except Exception as e:
        print(f"❌ Критическая ошибка в super_admin_rations: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        }, status=500)





@api_view(['GET'])
def super_admin_ration_detail(request, ration_id):
    """Получить детальную информацию о рационе"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        ration = get_object_or_404(Ration, ration_id=ration_id)

        ration_data = {
            'ration_id': ration.ration_id,
            'calculation_date': ration.calculation_date.isoformat() if ration.calculation_date else None,
            'composition': ration.composition,
            'energy_content': ration.energy_content,
            'total_dmi': ration.total_dmi,
        }

        # Добавляем информацию о животном
        if ration.animal:
            ration_data['animal'] = {
                'animal_id': ration.animal.animal_id,
                'name': ration.animal.name,
                'sex': ration.animal.sex,
                'age': ration.animal.age,
                'estimated_weight': ration.animal.estimated_weight
            }

        # Добавляем информацию об анализе
        if ration.analysis:
            ration_data['analysis'] = {
                'analysis_id': ration.analysis.analysis_id,
                'analysis_date': ration.analysis.analysis_date.isoformat() if ration.analysis.analysis_date else None,
                'diagnosis': ration.analysis.diagnosis,
            }

            # Добавляем информацию о видео
            if ration.analysis.video:
                ration_data['video'] = {
                    'video_id': ration.analysis.video.video_id,
                    'file_path': ration.analysis.video.file_path,
                    'upload_date': ration.analysis.video.upload_date.isoformat() if ration.analysis.video.upload_date else None,
                }

                if ration.analysis.video.user:
                    ration_data['owner'] = {
                        'user_id': ration.analysis.video.user.user_id,
                        'login': ration.analysis.video.user.login,
                        'email': ration.analysis.video.user.email,
                        'full_name': ration.analysis.video.user.full_name
                    }

        return Response({
            'success': True,
            'ration': ration_data
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['DELETE'])
def super_admin_delete_ration(request, ration_id):
    """Удалить рацион"""
    if not is_super_admin(request):
        return Response({'success': False, 'error': 'Доступ запрещен'}, status=403)

    try:
        ration = get_object_or_404(Ration, ration_id=ration_id)
        ration.delete()

        return Response({
            'success': True,
            'message': 'Рацион удален успешно'
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
