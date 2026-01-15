"""
Утилиты для работы с пользователями и проверки прав
"""

def get_user_role(user):
    """Определяем роль пользователя"""
    if not user.is_authenticated:
        return 'guest'
    
    if user.is_superuser:
        return 'admin'
    
    # Здесь можно добавить проверку других ролей
    # Например, проверку групп или кастомных полей
    
    return 'user'

def get_menu_for_role(role):
    """Возвращает меню для конкретной роли"""
    # Базовые меню для каждой роли
    base_menus = {
        'guest': [
            {'url': '/', 'name': 'Главная', 'icon': '🏠'},
            {'url': '/login/', 'name': 'Войти', 'icon': '🔐'},
        ],
        'user': [
            {'url': '/', 'name': 'Главная', 'icon': '🏠'},
            {'url': '/my-animals/', 'name': 'Мои лошади', 'icon': '🐴'},
            {'url': '/video-upload/', 'name': 'Загрузить видео', 'icon': '📹'},
            {'url': '/my-analyses/', 'name': 'Мои анализы', 'icon': '📊'},
            {'url': '/profile/', 'name': 'Профиль', 'icon': '👤'},
        ],
        'admin': [
            {'url': '/', 'name': 'Главная', 'icon': '🏠'},
            {'url': '/dashboard/', 'name': 'Панель', 'icon': '📊'},
            {'url': '/admin/users/', 'name': 'Пользователи', 'icon': '👥'},
            {'url': '/admin/animals/', 'name': 'Все лошади', 'icon': '🐴'},
            {'url': '/admin/videos/', 'name': 'Все видео', 'icon': '📹'},
            {'url': '/admin/analyses/', 'name': 'Анализы', 'icon': '🔍'},
            {'url': '/admin/', 'name': 'Админка', 'icon': '⚙️'},
        ]
    }
    
    return base_menus.get(role, base_menus['guest'])
    """Возвращает меню для конкретной роли"""
    menus = {
        'guest': [
            {'url': '/', 'name': 'Главная', 'icon': '🏠'},
            {'url': '/login/', 'name': 'Войти', 'icon': '🔐'},
        ],
        'user': [
            {'url': '/', 'name': 'Главная', 'icon': '🏠'},
            {'url': '/my-animals/', 'name': 'Мои лошади', 'icon': '🐴'},
            {'url': '/video-upload/', 'name': 'Загрузить видео', 'icon': '📹'},
            {'url': '/my-analyses/', 'name': 'Мои анализы', 'icon': '📊'},
            {'url': '/profile/', 'name': 'Профиль', 'icon': '👤'},
        ],
        'admin': [
            {'url': '/', 'name': 'Главная', 'icon': '🏠'},
            {'url': '/dashboard/', 'name': 'Панель', 'icon': '📊'},
            {'url': '/admin/users/', 'name': 'Пользователи', 'icon': '👥'},
            {'url': '/admin/animals/', 'name': 'Все лошади', 'icon': '🐴'},
            {'url': '/admin/videos/', 'name': 'Все видео', 'icon': '📹'},
            {'url': '/admin/analyses/', 'name': 'Анализы', 'icon': '🔍'},
            {'url': '/admin/', 'name': 'Админка', 'icon': '⚙️'},
        ]
    }
    return menus.get(role, menus['guest'])

def can_user_access(user, required_role):
    """Проверяет имеет ли пользователь доступ"""
    user_role = get_user_role(user)
    role_hierarchy = ['guest', 'user', 'admin']
    
    user_index = role_hierarchy.index(user_role)
    required_index = role_hierarchy.index(required_role)
    
    return user_index >= required_index

def get_user_animals(user):
    """Возвращает животных пользователя"""
    if not user.is_authenticated:
        return []
    
    from web.database.models import Animal
    
    if user.is_superuser:
        # Админ видит всех животных
        return Animal.objects.all()
    else:
        # Обычный пользователь видит только своих
        return Animal.objects.filter(user=user)
