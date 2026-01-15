
import pytz
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

class TimezoneMiddleware(MiddlewareMixin):
    """Middleware для установки часового пояса"""
    
    def process_request(self, request):
        # Устанавливаем часовой пояс по умолчанию
        timezone.activate(pytz.timezone('Europe/Moscow'))
        
    def process_response(self, request, response):
        # Деактивируем часовой пояс после обработки
        timezone.deactivate()
        return response
