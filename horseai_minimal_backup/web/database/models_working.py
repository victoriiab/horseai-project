from django.db import models

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    login = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    email = models.CharField(max_length=254, unique=True)
    full_name = models.CharField(max_length=100)
    role_id = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'database_user'

class Animal(models.Model):
    animal_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    sex = models.CharField(max_length=10, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    estimated_weight = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'database_animal'

class Video(models.Model):
    video_id = models.AutoField(primary_key=True)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_path = models.CharField(max_length=255)
    upload_date = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField(blank=True, null=True)
    resolution = models.CharField(max_length=50, blank=True, null=True)
    analysis_status = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'database_video'

class Analysis(models.Model):
    analysis_id = models.AutoField(primary_key=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    posture = models.CharField(max_length=50, blank=True, null=True)
    gait_quality = models.CharField(max_length=50, blank=True, null=True)
    size_category = models.CharField(max_length=20, blank=True, null=True)
    estimated_weight = models.FloatField(blank=True, null=True)
    confidence_score = models.FloatField(blank=True, null=True)
    analysis_date = models.DateTimeField(auto_now_add=True)
    is_lame = models.BooleanField(blank=True, null=True)
    lameness_probability = models.FloatField(blank=True, null=True)
    lameness_confidence = models.FloatField(blank=True, null=True)
    diagnosis = models.TextField(blank=True, null=True)
    diagnosis_note = models.TextField(blank=True, null=True)
    analysis_video_path = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'database_analysis'

class Feed(models.Model):
    feed_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    dry_matter = models.FloatField(blank=True, null=True)
    energy = models.FloatField(blank=True, null=True)
    protein = models.FloatField(blank=True, null=True)
    fiber = models.FloatField(blank=True, null=True)
    price_per_kg = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'database_feed'

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
