from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Horse(models.Model):
    """Модель лошади"""
    GENDER_CHOICES = [
        ('M', 'Жеребец'),
        ('F', 'Кобыла'),
        ('G', 'Мерин'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name="Кличка")
    breed = models.CharField(max_length=100, blank=True, verbose_name="Порода")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Пол")
    age = models.IntegerField(verbose_name="Возраст (лет)")
    weight = models.FloatField(verbose_name="Вес (кг)")
    color = models.CharField(max_length=50, blank=True, verbose_name="Масть")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_gender_display()}, {self.age} лет)"
    
    class Meta:
        verbose_name = "Лошадь"
        verbose_name_plural = "Лошади"

class VideoAnalysis(models.Model):
    """Модель анализа видео"""
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('processing', 'В обработке'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
    ]
    
    SEVERITY_CHOICES = [
        ('healthy', 'Здоровая'),
        ('mild', 'Легкая'),
        ('moderate', 'Умеренная'),
        ('severe', 'Тяжелая'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    horse = models.ForeignKey(Horse, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Лошадь")
    
    # Информация о видео
    video_name = models.CharField(max_length=255, verbose_name="Название видео")
    video_path = models.CharField(max_length=500, verbose_name="Путь к видео")
    video_id = models.CharField(max_length=100, unique=True, verbose_name="ID видео")
    
    # Результаты анализа
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    lameness_probability = models.FloatField(default=0, verbose_name="Вероятность хромоты (%)")
    confidence = models.FloatField(default=0, verbose_name="Уверенность анализа (%)")
    diagnosis = models.CharField(max_length=200, blank=True, verbose_name="Диагноз")
    diagnosis_note = models.TextField(blank=True, verbose_name="Примечание к диагнозу")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, blank=True, verbose_name="Степень тяжести")
    
    # Технические данные
    processing_time = models.FloatField(default=0, verbose_name="Время обработки (сек)")
    frames_analyzed = models.IntegerField(default=0, verbose_name="Кадров проанализировано")
    features_extracted = models.IntegerField(default=0, verbose_name="Признаков извлечено")
    
    # JSON данные
    result_data = models.JSONField(default=dict, verbose_name="Данные результата")
    features_data = models.JSONField(default=dict, verbose_name="Данные признаков")
    
    # Даты
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Анализ {self.video_id} - {self.get_status_display()}"
    
    def get_severity_color(self):
        colors = {
            'healthy': 'success',
            'mild': 'info',
            'moderate': 'warning',
            'severe': 'danger'
        }
        return colors.get(self.severity, 'secondary')
    
    def get_status_icon(self):
        icons = {
            'pending': 'clock',
            'processing': 'sync fa-spin',
            'completed': 'check-circle',
            'failed': 'exclamation-circle'
        }
        return icons.get(self.status, 'question')
    
    class Meta:
        verbose_name = "Анализ видео"
        verbose_name_plural = "Анализы видео"
        ordering = ['-created_at']
