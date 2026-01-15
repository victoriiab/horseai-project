from django.db import models

# ОТДЕЛЬНАЯ модель для хромоты - не трогаем существующие!
class LamenessAnalysis(models.Model):
    lameness_id = models.AutoField(primary_key=True)
    video = models.ForeignKey('database.Video', models.DO_NOTHING, db_column='video_id')
    analysis_date = models.DateTimeField(auto_now_add=True)
    
    # Результаты анализа
    is_lame = models.BooleanField(null=True, blank=True)
    lameness_probability = models.FloatField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    diagnosis = models.CharField(max_length=100, blank=True)
    diagnosis_note = models.TextField(blank=True)
    
    # Статус
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Ожидает'),
        ('processing', 'В процессе'), 
        ('completed', 'Завершен'),
        ('failed', 'Ошибка')
    ])
    
    class Meta:
        managed = False
        db_table = 'database_lameness_analysis'

# ОТДЕЛЬНАЯ модель для признаков походки
class LamenessGaitFeatures(models.Model):
    feature_id = models.AutoField(primary_key=True)
    lameness_analysis = models.ForeignKey(LamenessAnalysis, models.DO_NOTHING, db_column='lameness_id')
    
    # Признаки из вашего детектора
    front_asymmetry = models.FloatField()
    back_asymmetry = models.FloatField()
    min_amplitude = models.FloatField()
    back_front_ratio = models.FloatField()
    front_left_var = models.FloatField()
    front_right_var = models.FloatField()
    front_sync = models.FloatField()
    back_sync = models.FloatField()
    diagonal_sync = models.FloatField()
    front_velocity = models.FloatField()
    front_jerk = models.FloatField()
    total_rom = models.FloatField()
    
    class Meta:
        managed = False
        db_table = 'database_lameness_features'
