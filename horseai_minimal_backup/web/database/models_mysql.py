from django.db import models

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    login = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    email = models.CharField(max_length=254, unique=True)
    full_name = models.CharField(max_length=100)
    role_id = models.CharField(max_length=10)
    created_at = models.DateTimeField()
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'database_user'  # В MySQL таблица с префиксом!

class Animal(models.Model):
    animal_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING)
    name = models.CharField(max_length=50)
    sex = models.CharField(max_length=10, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    estimated_weight = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'database_animal'

class Video(models.Model):
    video_id = models.AutoField(primary_key=True)
    animal = models.ForeignKey(Animal, models.DO_NOTHING)
    user = models.ForeignKey(User, models.DO_NOTHING)
    file_path = models.CharField(max_length=255)
    upload_date = models.DateTimeField()
    duration = models.FloatField()
    resolution = models.CharField(max_length=50)
    analysis_status = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'database_video'

class Analysis(models.Model):
    analysis_id = models.AutoField(primary_key=True)
    video = models.ForeignKey(Video, models.DO_NOTHING)
    posture = models.CharField(max_length=50, blank=True, null=True)
    gait_quality = models.CharField(max_length=50, blank=True, null=True)
    size_category = models.CharField(max_length=20, blank=True, null=True)
    estimated_weight = models.FloatField(blank=True, null=True)
    confidence_score = models.FloatField(blank=True, null=True)
    analysis_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
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
        managed = False
        db_table = 'database_feed'

class Ration(models.Model):
    ration_id = models.AutoField(primary_key=True)
    animal = models.ForeignKey(Animal, models.DO_NOTHING)
    analysis = models.ForeignKey(Analysis, models.DO_NOTHING, blank=True, null=True)
    total_dmi = models.FloatField(blank=True, null=True)
    energy_content = models.FloatField(blank=True, null=True)
    calculation_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'database_ration'
