from django.db import models

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    login = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    email = models.CharField(max_length=254, unique=True)
    full_name = models.CharField(max_length=100)
    role_id = models.CharField(max_length=10, choices=[
        ('admin', 'Администратор'),
        ('user', 'Пользователь')
    ], default='user')
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    class Meta:
        db_table = 'database_user'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.login

class Animal(models.Model):
    animal_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    sex = models.CharField(max_length=10, choices=[
        ('male', 'Жеребец'),
        ('female', 'Кобыла'),
        ('gelding', 'Мерин'),
        ('unknown', 'Не указан')
    ], blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    estimated_weight = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'database_animal'
        verbose_name = 'Животное'
        verbose_name_plural = 'Животные'

    def __str__(self):
        return self.name

class Video(models.Model):
    video_id = models.AutoField(primary_key=True)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_path = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    upload_date = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField(blank=True, null=True)
    resolution = models.CharField(max_length=50, blank=True, null=True)
    analysis_status = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('pending', 'В ожидании'),
        ('processing', 'В обработке'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка')
    ], default='pending')

    class Meta:
        db_table = 'database_video'
        verbose_name = 'Видео'
        verbose_name_plural = 'Видео'

    def __str__(self):
        return f"{self.original_filename} ({self.video_id})"

class Analysis(models.Model):
    analysis_id = models.AutoField(primary_key=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    
    # Основные поля
    posture = models.CharField(max_length=50, blank=True, null=True)
    gait_quality = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('normal', 'Норма'),
        ('poor', 'Плохая'),
        ('good', 'Хорошая')
    ])
    size_category = models.CharField(max_length=20, blank=True, null=True)
    estimated_weight = models.FloatField(blank=True, null=True)
    confidence_score = models.FloatField(blank=True, null=True)
    analysis_date = models.DateTimeField(auto_now_add=True)

    # Поля для хромоты
    is_lame = models.BooleanField(default=False)
    lameness_probability = models.FloatField(default=0.0)
    lameness_confidence = models.FloatField(default=0.0)
    diagnosis = models.TextField(blank=True, null=True)
    diagnosis_note = models.TextField(blank=True, null=True)
    analysis_video_path = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'database_analysis'
        verbose_name = 'Анализ'
        verbose_name_plural = 'Анализы'

    def __str__(self):
        status = "Хромая" if self.is_lame else "Здоровая"
        return f"Анализ {self.analysis_id} ({status})"

class Feed(models.Model):
    feed_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=[
        ('hay', 'Сено'),
        ('concentrate', 'Концентрат'),
        ('additive', 'Добавка'),
        ('other', 'Другое')
    ])
    dry_matter = models.FloatField(blank=True, null=True)
    energy = models.FloatField(blank=True, null=True)
    protein = models.FloatField(blank=True, null=True)
    fiber = models.FloatField(blank=True, null=True)
    price_per_kg = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'database_feed'
        verbose_name = 'Корм'
        verbose_name_plural = 'Корма'

    def __str__(self):
        return self.name

class Ration(models.Model):
    ration_id = models.AutoField(primary_key=True)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    analysis = models.ForeignKey(Analysis, on_delete=models.SET_NULL, blank=True, null=True)
    total_dmi = models.FloatField(blank=True, null=True)
    energy_content = models.FloatField(blank=True, null=True)
    calculation_date = models.DateTimeField(auto_now_add=True)
    composition = models.JSONField(blank=True, null=True, default=dict)

    class Meta:
        db_table = 'database_ration'
        ordering = ["-calculation_date"]
        verbose_name = 'Рацион'
        verbose_name_plural = 'Рационы'

    def __str__(self):
        return f"Рацион {self.ration_id} для {self.animal.name}"

class RationHistory(models.Model):
    """История изменений рационов"""
    history_id = models.AutoField(primary_key=True)
    ration = models.ForeignKey(Ration, on_delete=models.CASCADE, related_name='history')
    previous_composition = models.JSONField(default=dict)  # Исправляем на JSONField
    new_composition = models.JSONField(default=dict)       # Исправляем на JSONField
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_date = models.DateTimeField(auto_now_add=True)
    change_type = models.CharField(max_length=20, choices=[
        ('created', 'Создан'),
        ('updated', 'Обновлен'),
        ('deleted', 'Удален'),
        ('calculated', 'Рассчитан системой'),
    ])
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'database_ration_history'
        ordering = ['-change_date']
        verbose_name = 'История рациона'
        verbose_name_plural = 'История рационов'
    
    def __str__(self):
        return f"Изменение рациона #{self.ration_id} от {self.change_date}"

class AnimalHealthHistory(models.Model):
    """История здоровья животного"""
    history_id = models.AutoField(primary_key=True)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='health_history')
    analysis = models.ForeignKey(Analysis, on_delete=models.SET_NULL, null=True, blank=True)
    recorded_date = models.DateTimeField(auto_now_add=True)
    
    # Показатели здоровья
    lameness_status = models.CharField(max_length=50, choices=[
        ('healthy', 'Здорова'),
        ('suspected', 'Подозрение на хромоту'),
        ('lame', 'Хромая'),
    ])
    lameness_probability = models.FloatField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    body_condition_score = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'database_animal_health_history'
        ordering = ['-recorded_date']
        verbose_name = 'История здоровья'
        verbose_name_plural = 'История здоровья животных'
    
    def __str__(self):
        return f"{self.animal.name} - {self.get_lameness_status_display()} ({self.recorded_date.date()})"

# Модель LamenessAnalysis из предыдущей версии (если нужна)
class LamenessAnalysis(models.Model):
    """Анализ хромоты (дополнительная модель)"""
    analysis_id = models.AutoField(primary_key=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, null=True, blank=True)
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('processing', 'В обработке'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Результаты
    is_lame = models.BooleanField(blank=True, null=True)
    lameness_probability = models.FloatField(blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)
    diagnosis = models.TextField(blank=True, null=True)
    diagnosis_note = models.TextField(blank=True, null=True)
    
    # Файлы результатов
    result_file = models.FileField(upload_to='analysis/results/', blank=True, null=True)
    plot_file = models.FileField(upload_to='analysis/plots/', blank=True, null=True)
    annotated_video = models.FileField(upload_to='analysis/videos/', blank=True, null=True)
    h5_file = models.FileField(upload_to='analysis/data/', blank=True, null=True)
    
    # Логи
    analysis_log = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'database_lameness_analysis'
        verbose_name = 'Анализ хромоты'
        verbose_name_plural = 'Анализы хромоты'

    def __str__(self):
        return f"{self.original_filename} ({self.get_status_display()})"
