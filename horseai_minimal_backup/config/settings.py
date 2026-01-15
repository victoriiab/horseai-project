import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key-here'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'web.database',
    'scripts.api',
    'frontend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# ПОДКЛЮЧЕНИЕ К MYSQL С ДАННЫМИ
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'horseai_db',
        'USER': 'root',
        'PASSWORD': 'KVA437',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Yekaterinburg'
USE_I18N = True
USE_TZ = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'frontend.context_processors.menu_items',
                'frontend.context_processors.user_role',
            ],
        },
    },
]

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}

if DEBUG:
    CSRF_TRUSTED_ORIGINS = [
    'http://192.168.56.56:8000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    ]
    CORS_ALLOW_ALL_ORIGINS = True
    CSRF_COOKIE_SECURE = False
#CSRF_TRUSTED_ORIGINS = []
#CORS_ALLOW_ALL_ORIGINS =False
#CSRF_COOKIE_SECURE = False



# Увеличиваем максимальный размер загружаемого файла (до 500MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000  # 500 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 524288000  # 500 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240    # Увеличиваем количество полей

# Увеличиваем timeout для больших файлов
SESSION_COOKIE_AGE = 3600  # 1 час
SESSION_SAVE_EVERY_REQUEST = True

# Настройки messages
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

# Настройки авторизации
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

print("✅ Настройки для больших файлов применены")



# Инициализация ML процессора при запуске Django
def start_ml_processor():
    try:
        from ml_processing.ml_integrator import start_ml_processor
        processor = start_ml_processor()
        print("✅ ML Processor started successfully")
        return processor
    except Exception as e:
        print(f"⚠️ Failed to start ML Processor: {e}")
        return None

# Запускаем при старте (для production используйте management command)
if not os.environ.get('RUN_MAIN'):
    ml_processor = start_ml_processor()

# Настройки для обработки видео
MAX_VIDEO_SIZE = 524288000  # 500MB
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
VIDEO_PROCESSING = {
    'CONVERT_TO_MP4': True,  # Автоматически конвертировать в MP4
    'OUTPUT_CODEC': 'libx264',
    'OUTPUT_PRESET': 'fast',
    'OUTPUT_CRF': 23,
}
