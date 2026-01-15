from django.apps import AppConfig

class DatabaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web.database'
    
    def ready(self):
        # Импортируем сигналы
        import web.database.signals
