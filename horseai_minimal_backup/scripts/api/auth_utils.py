"""
Утилиты для проверки доступа пользователей
"""

def check_user_access(request_user, video_user_login):
    """
    Проверяет, имеет ли пользователь доступ к данным
    """
    # Простая проверка: пользователь имеет доступ если логин совпадает
    # или если пользователь администратор
    if request_user.username == video_user_login:
        return True
    
    # Проверка на администратора (если есть группа или флаг)
    if hasattr(request_user, 'is_staff') and request_user.is_staff:
        return True
    
    return False
