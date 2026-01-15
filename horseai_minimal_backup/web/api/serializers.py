from rest_framework import serializers
from web.database.models import User, Animal, Video, Analysis, Feed, Ration

# Переводчик для пользователей
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User 
        fields = ['user_id', 'login', 'email', 'full_name', 'role_id', 'created_at']

        read_only_fields = ['user_id', 'created_at']  

# Переводчик для животных  
class AnimalSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Animal
        fields = ['animal_id', 'name', 'sex', 'age', 'estimated_weight', 'user', 'owner_name', 'created_at']
        read_only_fields = ['animal_id', 'created_at']

# Переводчик для видео
class VideoSerializer(serializers.ModelSerializer):
    animal_name = serializers.CharField(source='animal.name', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Video
        fields = ['video_id', 'animal', 'animal_name', 'user', 'user_name', 'file_path', 
                 'upload_date', 'duration', 'resolution']
        read_only_fields = ['video_id', 'upload_date']

# Переводчик для анализов
class AnalysisSerializer(serializers.ModelSerializer):
    animal_name = serializers.CharField(source='video.animal.name', read_only=True)
    
    class Meta:
        model = Analysis
        fields = ['analysis_id', 'video', 'animal_name', 'posture', 'gait_quality', 
                 'size_category', 'estimated_weight', 'confidence_score', 'analysis_date']
        read_only_fields = ['analysis_id', 'analysis_date']

# Переводчик для кормов
class FeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feed
        fields = ['feed_id', 'name', 'type', 'dry_matter', 'energy', 'protein', 
                 'fiber', 'price_per_kg']
        read_only_fields = ['feed_id']

# Переводчик для рационов
class RationSerializer(serializers.ModelSerializer):
    animal_name = serializers.CharField(source='animal.name', read_only=True)
    
    class Meta:
        model = Ration
        fields = ['ration_id', 'animal', 'animal_name', 'analysis', 'total_dmi', 
                 'energy_content', 'composition', 'calculation_date']
        read_only_fields = ['ration_id', 'calculation_date']