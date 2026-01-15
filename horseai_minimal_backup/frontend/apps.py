from django.apps import AppConfig


class FrontendConfig(AppConfig):
    def ready(self):
        """Автоматическая синхронизация пользователей при запуске"""
        import os
        if os.environ.get('RUN_MAIN') == 'true':
            try:
                from django.contrib.auth.models import User as AuthUser
                from web.database.models import User as CustomUser
                from django.utils import timezone
                
                print("🔄 Проверяем синхронизацию пользователей...")
                
                # Синхронизируем всех AuthUser с CustomUser
                for auth_user in AuthUser.objects.all():
                    try:
                        custom_user = CustomUser.objects.get(login=auth_user.username)
                        # Обновляем поля
                        custom_user.email = auth_user.email or ''
                        custom_user.is_active = auth_user.is_active
                        custom_user.is_staff = auth_user.is_staff
                        custom_user.is_superuser = auth_user.is_superuser
                        if auth_user.last_login:
                            custom_user.last_login = auth_user.last_login
                        custom_user.save()
                    except CustomUser.DoesNotExist:
                        # Создаем нового
                        CustomUser.objects.create(
                            login=auth_user.username,
                            email=auth_user.email or '',
                            password_hash=auth_user.password,
                            full_name=auth_user.username,
                            role_id='user',
                            created_at=timezone.now(),
                            last_login=auth_user.last_login or timezone.now(),
                            is_active=auth_user.is_active,
                            is_staff=auth_user.is_staff,
                            is_superuser=auth_user.is_superuser
                        )
                        print(f"✅ Создан CustomUser для {auth_user.username}")
                
                print("✅ Синхронизация пользователей завершена")
            except Exception as e:
                print(f"⚠️ Ошибка синхронизации: {e}")
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'frontend'
