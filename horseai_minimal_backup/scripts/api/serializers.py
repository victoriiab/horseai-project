from rest_framework import serializers
from web.database.models import Animal, Video, Analysis, Feed, Ration, User, LamenessAnalysis

class AnimalSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Animal
        fields = '__all__'
        read_only_fields = ('animal_id', 'created_at')

class VideoSerializer(serializers.ModelSerializer):
    animal_name = serializers.CharField(source='animal.name', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Video
        fields = '__all__'
        read_only_fields = ('video_id', 'upload_date')

class AnalysisSerializer(serializers.ModelSerializer):
    animal_name = serializers.CharField(source='video.animal.name', read_only=True)
    video_file = serializers.CharField(source='video.file_path', read_only=True)
    user_name = serializers.CharField(source='video.user.full_name', read_only=True)

    class Meta:
        model = Analysis
        fields = '__all__'

class LamenessAnalysisSerializer(serializers.ModelSerializer):
    animal_name = serializers.CharField(source='animal.name', read_only=True)
    video_filename = serializers.CharField(source='video.filename', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = LamenessAnalysis
        fields = [
            'id', 'analysis_id', 'video_id', 'animal_id', 'user_id',
            'lameness_score', 'lameness_type', 'affected_limbs',
            'asymmetry_metrics', 'motion_features', 'recommendations',
            'created_at', 'updated_at', 'animal_name', 'video_filename', 'user_name'
        ]

class FeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feed
        fields = '__all__'

class RationSerializer(serializers.ModelSerializer):
    animal_name = serializers.SerializerMethodField()
    animal_weight = serializers.SerializerMethodField()
    formatted_date = serializers.SerializerMethodField()

    class Meta:
        model = Ration
        fields = [
            'ration_id', 'animal', 'analysis', 'total_dmi',
            'energy_content', 'calculation_date', 'composition',
            'animal_name', 'animal_weight', 'formatted_date'
        ]

    def get_animal_name(self, obj):
        return obj.animal.name if obj.animal else 'Неизвестно'

    def get_animal_weight(self, obj):
        return obj.animal.estimated_weight if obj.animal else 0

    def get_formatted_date(self, obj):
        if obj.calculation_date:
            return obj.calculation_date.strftime('%d.%m.%Y %H:%M')
        return ''

    def to_representation(self, instance):
        """Преобразование для API"""
        representation = super().to_representation(instance)

        # Добавляем состав в удобном формате
        if instance.composition:
            representation['composition_details'] = {
                'hay': f"{instance.composition.get('hay_amount', 0)} кг/день",
                'grain': f"{instance.composition.get('grain_amount', 0)} кг/день",
                'supplements': f"{instance.composition.get('supplement_amount', 0)} кг/день",
                'total_cost': f"{instance.composition.get('total_month_cost', 0)} руб/месяц",
                'lameness': instance.composition.get('lameness', 'none')
            }

        return representation

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'login', 'email', 'full_name', 'role', 'created_at', 'last_login']
