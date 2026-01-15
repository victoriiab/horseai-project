from django.contrib.auth.hashers import make_password, check_password
from .models import User, Animal, Video, Analysis, Feed, Ration
from django.utils import timezone

# ----------------------------
# USER CRUD
# ----------------------------

def create_user(login, password, email, full_name, role_id="owner"):
    """Регистрация пользователя"""
    user = User(
        login=login,
        password_hash=make_password(password),
        email=email,
        full_name=full_name,
        role_id=role_id
    )
    user.save()
    return user


def get_user_profile(user_id):
    """Просмотр профиля пользователя"""
    return User.objects.filter(user_id=user_id).first()


def update_user(user_id, email=None, full_name=None, new_password=None):
    """Изменение данных пользователя"""
    user = User.objects.filter(user_id=user_id).first()
    if not user:
        return None

    if email:
        user.email = email
    if full_name:
        user.full_name = full_name
    if new_password:
        user.password_hash = make_password(new_password)
    user.save()
    return user


def delete_user(admin_user, target_user_id):
    """Удаление аккаунта (только администратор)"""
    if admin_user.role_id != "admin":
        raise PermissionError("Удаление пользователей разрешено только администратору.")
    User.objects.filter(user_id=target_user_id).delete()

# ----------------------------
# ANIMAL CRUD
# ----------------------------

def create_animal(user, name, sex=None, age=None, estimated_weight=None):
    """Создание карточки животного (автоматически системой после анализа видео)"""
    animal = Animal.objects.create(
        user=user,
        name=name,
        sex=sex,
        age=age,
        estimated_weight=estimated_weight,
        created_at=timezone.now()
    )
    return animal


def get_animal(animal_id):
    """Просмотр карточки животного"""
    return Animal.objects.filter(animal_id=animal_id).first()


def update_animal(animal_id, name=None, estimated_weight=None):
    """Редактирование клички или массы"""
    animal = Animal.objects.filter(animal_id=animal_id).first()
    if not animal:
        return None
    if name:
        animal.name = name
    if estimated_weight:
        animal.estimated_weight = estimated_weight
    animal.save()
    return animal


def delete_animal(admin_user, animal_id):
    """Удаление животного (только администратор)"""
    if admin_user.role_id != "admin":
        raise PermissionError("Удаление животных разрешено только администратору.")
    Animal.objects.filter(animal_id=animal_id).delete()

# ----------------------------
# VIDEO CRUD
# ----------------------------

def upload_video(user, animal, file_path, duration, resolution):
    """Создание (загрузка) видео"""
    return Video.objects.create(
        user=user,
        animal=animal,
        file_path=file_path,
        duration=duration,
        resolution=resolution
    )


def get_video(video_id):
    """Просмотр видео"""
    return Video.objects.filter(video_id=video_id).first()


def update_video(video_id, new_path=None, resolution=None):
    """Изменение метаданных видео"""
    video = Video.objects.filter(video_id=video_id).first()
    if not video:
        return None
    if new_path:
        video.file_path = new_path
    if resolution:
        video.resolution = resolution
    video.save()
    return video


def delete_video(user, video_id):
    """Удаление видео (владелец может удалить своё)"""
    video = Video.objects.filter(video_id=video_id, user=user).first()
    if video:
        video.delete()

# ----------------------------
# ANALYSIS CRUD
# ----------------------------

def create_analysis(video, posture, gait_quality, size_category, estimated_weight, confidence_score):
    """Создание анализа после обработки видео"""
    return Analysis.objects.create(
        video=video,
        posture=posture,
        gait_quality=gait_quality,
        size_category=size_category,
        estimated_weight=estimated_weight,
        confidence_score=confidence_score
    )


def get_analysis(analysis_id):
    """Просмотр анализа"""
    return Analysis.objects.filter(analysis_id=analysis_id).first()


def delete_analysis(admin_user, analysis_id):
    """Удаление анализа (только администратор)"""
    if admin_user.role_id != "admin":
        raise PermissionError("Удаление анализов разрешено только администратору.")
    Analysis.objects.filter(analysis_id=analysis_id).delete()

# ----------------------------
# RATION CRUD
# ----------------------------

def create_ration(animal, analysis, total_dmi, energy_content, composition):
    """Создание рациона на основе анализа"""
    return Ration.objects.create(
        animal=animal,
        analysis=analysis,
        total_dmi=total_dmi,
        energy_content=energy_content,
        composition=composition
    )


def get_ration(ration_id):
    """Просмотр рациона"""
    return Ration.objects.filter(ration_id=ration_id).first()


def update_ration(ration_id, total_dmi=None, energy_content=None, composition=None):
    """Корректировка пользователем"""
    ration = Ration.objects.filter(ration_id=ration_id).first()
    if not ration:
        return None
    if total_dmi:
        ration.total_dmi = total_dmi
    if energy_content:
        ration.energy_content = energy_content
    if composition:
        ration.composition = composition
    ration.save()
    return ration


def delete_ration(ration_id):
    """Удаление рациона пользователем"""
    Ration.objects.filter(ration_id=ration_id).delete()

# ----------------------------
# FEED CRUD
# ----------------------------

def create_feed(admin_user, name, type, dry_matter, energy, protein, fiber, price_per_kg):
    """Добавление корма (только администратор)"""
    if admin_user.role_id != "admin":
        raise PermissionError("Добавление корма разрешено только администратору.")
    return Feed.objects.create(
        name=name,
        type=type,
        dry_matter=dry_matter,
        energy=energy,
        protein=protein,
        fiber=fiber,
        price_per_kg=price_per_kg
    )


def get_all_feeds():
    """Просмотр справочника кормов"""
    return Feed.objects.all()


def update_feed(admin_user, feed_id, **kwargs):
    """Редактирование данных корма (только администратор)"""
    if admin_user.role_id != "admin":
        raise PermissionError("Изменение справочника разрешено только администратору.")
    feed = Feed.objects.filter(feed_id=feed_id).first()
    if feed:
        for key, value in kwargs.items():
            setattr(feed, key, value)
        feed.save()
    return feed


def delete_feed(admin_user, feed_id):
    """Удаление корма (только администратор)"""
    if admin_user.role_id != "admin":
        raise PermissionError("Удаление разрешено только администратору.")
    Feed.objects.filter(feed_id=feed_id).delete()

# ============================================
# ЛОГИКА РАСЧЕТА РАЦИОНОВ ДЛЯ ЛОШАДЕЙ
# ============================================

def calculate_ration_for_animal(animal, analysis=None):
    """
    Рассчитывает рацион для лошади на основе веса и анализа
    """
    # Базовый расчет DMI (Dry Matter Intake - Потребление сухого вещества)
    # Формула: DMI = Вес_лошади * 0.025 (2.5% от веса тела)
    weight = animal.estimated_weight or 500  # кг, если вес не указан
    
    base_dmi = weight * 0.025  # кг/день
    
    # Корректировка на основе анализа (если есть)
    if analysis:
        # Корректировка по осанке и качеству походки
        if analysis.posture and 'poor' in analysis.posture.lower():
            base_dmi *= 0.95  # Уменьшаем на 5% при плохой осанке
        
        if analysis.gait_quality and 'poor' in analysis.gait_quality.lower():
            base_dmi *= 0.93  # Уменьшаем на 7% при плохой походке
            
        # Корректировка по категории размера
        if analysis.size_category:
            if 'large' in analysis.size_category.lower():
                base_dmi *= 1.1  # +10% для крупных
            elif 'small' in analysis.size_category.lower():
                base_dmi *= 0.9  # -10% для мелких
    
    # Расчет энергии (МДж/день)
    # Формула: Энергия = DMI * 1.25 (примерный коэффициент)
    energy = base_dmi * 1.25
    
    # Состав рациона (проценты от DMI)
    composition = {
        'hay': round(base_dmi * 0.55, 2),       # 55% сено
        'oats': round(base_dmi * 0.18, 2),      # 18% овес
        'bran': round(base_dmi * 0.07, 2),      # 7% отруби
        'carrot': round(base_dmi * 0.14, 2),    # 14% морковь
        'premix': round(base_dmi * 0.06, 2)     # 6% премикс
    }
    
    return {
        'total_dmi': round(base_dmi, 2),
        'energy_content': round(energy, 2),
        'composition': composition,
        'animal_id': animal.animal_id,
        'animal_name': animal.name,
        'weight_used': weight
    }


def create_ration_from_analysis(analysis_id):
    """
    Создает рацион на основе анализа видео
    """
    from web.database.models import Analysis, Animal, Ration
    from django.utils import timezone
    
    try:
        analysis = Analysis.objects.get(pk=analysis_id)
        animal = analysis.video.animal
        
        # Рассчитываем рацион
        ration_data = calculate_ration_for_animal(animal, analysis)
        
        # Создаем запись в БД
        ration = Ration.objects.create(
            animal=animal,
            analysis=analysis,
            total_dmi=ration_data['total_dmi'],
            energy_content=ration_data['energy_content'],
            composition=ration_data['composition'],
            calculation_date=timezone.now()
        )
        
        return {
            'success': True,
            'ration_id': ration.ration_id,
            'message': 'Рацион успешно создан',
            'data': ration_data
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Ошибка при создании рациона'
        }
