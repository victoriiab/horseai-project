"""
Сигналы для автоматической синхронизации пользователей
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import User as CustomUser
import datetime

@receiver(post_save, sender=User)
def create_custom_user_on_auth_user_create(sender, instance, created, **kwargs):
    """При создании Django пользователя создаем соответствующего CustomUser"""
    if created:
        # Определяем роль
        if instance.is_superuser:
            role_id = 'admin'
        else:
            role_id = 'user'
        
        # Создаем CustomUser
        CustomUser.objects.create(
            login=instance.username,
            password_hash=instance.password,
            email=instance.email,
            full_name=f"{instance.first_name} {instance.last_name}".strip() or instance.username,
            role_id=role_id,
            created_at=datetime.datetime.now(),
            last_login=instance.last_login
        )
        print(f"✅ Автоматически создан CustomUser для {instance.username}")

@receiver(post_save, sender=User)
def update_custom_user_on_auth_user_update(sender, instance, created, **kwargs):
    """При обновлении Django пользователя обновляем CustomUser"""
    if not created:
        try:
            custom_user = CustomUser.objects.get(login=instance.username)
            custom_user.email = instance.email
            custom_user.password_hash = instance.password
            custom_user.last_login = instance.last_login
            custom_user.save()
            print(f"✅ Автоматически обновлен CustomUser для {instance.username}")
        except CustomUser.DoesNotExist:
            # Если CustomUser не существует, создаем
            create_custom_user_on_auth_user_create(sender, instance, True, **kwargs)
