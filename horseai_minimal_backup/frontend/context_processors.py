from web.database.models import User


def menu_items(request):
    """
    Контекст-процессор для меню навигации.
    Добавляет переменную 'menu_items' во все шаблоны.
    """
    if not request.user.is_authenticated:
        items = [
            {'name': 'Главная', 'url': '/', 'icon': '🏠'},
            {'name': 'Войти', 'url': '/login/', 'icon': '🔐'},
            {'name': 'Регистрация', 'url': '/register/', 'icon': '📝'},
        ]
        return {'menu_items': items}
    
    is_admin = False
    try:
        custom_user = User.objects.get(login=request.user.username)
        if custom_user.role_id in ['admin', 'superadmin']:
            is_admin = True
    except User.DoesNotExist:
        if hasattr(request.user, 'is_staff') and request.user.is_staff:
            is_admin = True
    
    if is_admin:
        items = [
            {'name': 'Главная', 'url': '/', 'icon': '🏠'},
            {'name': 'Панель управления', 'url': '/super-admin/', 'icon': '🛡️'},
            {'name': 'Все животные', 'url': '/admin/database/animal/', 'icon': '🐴'},
            {'name': 'Все пользователи', 'url': '/admin/database/user/', 'icon': '👥'},
            {'name': 'Все видео', 'url': '/admin/database/video/', 'icon': '🎬'},
            {'name': 'Все анализы', 'url': '/admin/database/analysis/', 'icon': '📊'},
            {'name': 'Админ-панель Django', 'url': '/admin/', 'icon': '⚙️'},
        ]
    else:
        items = [
            {'name': 'Главная', 'url': '/', 'icon': '🏠'},
            {'name': 'Мои лошади', 'url': '/animals/', 'icon': '🐴'},
            {'name': 'Анализ походки', 'url': '/video-upload/', 'icon': '📹'},
            {'name': 'Результаты', 'url': '/analysis/results/', 'icon': '📊'},
            {'name': 'Рацион', 'url': '/ration/', 'icon': '🥗'},
            {'name': 'Профиль', 'url': '/profile/', 'icon': '👤'},
        ]
    
    return {'menu_items': items}


def user_role(request):
    """Роль пользователя - УПРОЩЕННАЯ версия"""
    if not request.user.is_authenticated:
        return {'user_role': 'guest'}
    
    try:
        custom_user = User.objects.get(login=request.user.username)
        if custom_user.role_id in ['admin', 'superadmin']:
            return {'user_role': 'admin'}
        elif custom_user.role_id == 'veterinarian':
            return {'user_role': 'veterinarian'}
        else:
            return {'user_role': 'user'}
    except User.DoesNotExist:
        if request.user.is_staff:
            return {'user_role': 'admin'}
        else:
            return {'user_role': 'user'}
    except Exception:
        return {'user_role': 'user'}
