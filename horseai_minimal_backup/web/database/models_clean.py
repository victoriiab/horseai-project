from django.db import models

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    login = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    email = models.CharField(max_length=254, unique=True)
    full_name = models.CharField(max_length=100)
    role_id = models.CharField(max_length=10, choices=[
        ('admin', 'Администратор'),
        ('owner', 'Владелец')
    ], default='owner')
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
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
    analysis_status = models.CharField(max_length=20, choices=[
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
        return f"{self.original_filename}"

class Analysis(models.Model):
    analysis_id = models.AutoField(primary_key=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    
    # Основные поля
    posture = models.CharField(max_length=50, blank=True, null=True)
    gait_quality = models.CharField(max_length=50, choices=[
        ('normal', 'Норма'),
        ('poor', 'Плохая'),
        ('good', 'Хорошая')
    ], default='normal')
    size_category = models.CharField(max_length=20, blank=True, null=True)
    estimated_weight = models.FloatField(blank=True, null=True)
    confidence_score = models.FloatField(default=0.0)
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
        return f"Анализ {self.analysis_id}"

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
        return f"Рацион {self.ration_id}"
