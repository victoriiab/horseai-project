from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User as DjangoUser
from web.database.models import User as CustomUser
from django.contrib.auth.hashers import check_password, make_password

class CustomAuthBackend(BaseBackend):
    """Аутентификация через кастомную таблицу database_user"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            custom_user = CustomUser.objects.get(login=username)

            if custom_user.password_hash and check_password(password, custom_user.password_hash):
                try:
                    django_user = DjangoUser.objects.get(username=username)
                except DjangoUser.DoesNotExist:
                    django_user = DjangoUser.objects.create_user(
                        username=username,
                        password=password, 
                        email=custom_user.email or '',
                        first_name=custom_user.full_name or '',
                        is_staff=custom_user.role_id in ['admin', 'superadmin'],
                        is_superuser=custom_user.role_id == 'superadmin'
                    )
                
                django_user.email = custom_user.email or django_user.email
                django_user.first_name = custom_user.full_name or django_user.first_name
                django_user.is_staff = custom_user.role_id in ['admin', 'superadmin']
                django_user.is_superuser = custom_user.role_id == 'superadmin'
                django_user.save()
                
                return django_user
        except CustomUser.DoesNotExist:
            return None
        except Exception as e:
            print(f"Ошибка аутентификации: {e}")
            return None
    
    def get_user(self, user_id):
        try:
            return DjangoUser.objects.get(pk=user_id)
        except DjangoUser.DoesNotExist:
            return None
