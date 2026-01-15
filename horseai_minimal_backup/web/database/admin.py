from django.contrib import admin
from .models import User, Animal, Video, Analysis, Feed, Ration

# ========== USER ADMIN ==========
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'login', 'email', 'full_name', 'role_id', 'created_at')
    list_filter = ('role_id', 'created_at')
    search_fields = ('login', 'email', 'full_name')
    ordering = ('-created_at',)
    
    # Упрощенные поля для редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': ('login', 'email', 'full_name', 'role_id')
        }),
        ('Дополнительно', {
            'fields': ('created_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    # Только для чтения поля
    readonly_fields = ('created_at', 'last_login')

# ========== ANIMAL ADMIN ==========
@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('animal_id', 'name', 'user', 'sex', 'age', 'estimated_weight', 'created_at')
    list_filter = ('sex', 'created_at')
    search_fields = ('name', 'user__login')
    raw_id_fields = ('user',)

# ========== VIDEO ADMIN ==========
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'animal', 'user', 'upload_date', 'duration', 'analysis_status')
    list_filter = ('analysis_status', 'upload_date')
    search_fields = ('animal__name', 'file_path')
    raw_id_fields = ('animal', 'user')

# ========== ANALYSIS ADMIN ==========
@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ('analysis_id', 'video', 'is_lame', 'lameness_probability', 'diagnosis', 'analysis_date')
    list_filter = ('is_lame', 'analysis_date')
    search_fields = ('video__animal__name', 'diagnosis')
    raw_id_fields = ('video',)

# ========== FEED ADMIN ==========
@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = ('feed_id', 'name', 'type', 'dry_matter', 'energy', 'protein', 'price_per_kg')
    list_filter = ('type',)
    search_fields = ('name',)

# ========== RATION ADMIN ==========
@admin.register(Ration)
class RationAdmin(admin.ModelAdmin):
    list_display = ('ration_id', 'animal', 'total_dmi', 'energy_content', 'calculation_date')
    list_filter = ('calculation_date',)
    search_fields = ('animal__name',)
    raw_id_fields = ('animal', 'analysis')

print("✅ Админка настроена корректно (без полей is_active, is_staff, is_superuser)")
