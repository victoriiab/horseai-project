"""
Утилиты для расчетов рационов и других операций
"""
from web.database.models import Feed, Ration, Analysis
from django.utils import timezone
import random

def calculate_ration(animal, weight):
    """Расчет рациона для животного"""
    try:
        # Базовый расчет: 2-3% от веса в сухом веществе
        total_dmi = float(weight) * 0.025  # 2.5%
        
        # Получаем корма из базы
        feeds = Feed.objects.all()
        
        composition = {}
        recommendations = []
        
        if feeds.exists():
            # Ищем сено
            hay = feeds.filter(type='сенo').first() or feeds.filter(type__contains='сен').first()
            if hay:
                hay_amount = total_dmi * 0.7
                composition['hay'] = {
                    'name': hay.name,
                    'amount_kg': round(hay_amount, 2),
                    'energy': hay.energy or 0,
                    'protein': hay.protein or 0
                }
                recommendations.append(f"Сено ({hay.name}): {hay_amount:.2f} кг/день")
            
            # Ищем концентраты
            concentrates = feeds.filter(type='концентрат').first() or feeds.filter(type__contains='конц').first()
            if concentrates:
                conc_amount = total_dmi * 0.25
                composition['concentrates'] = {
                    'name': concentrates.name,
                    'amount_kg': round(conc_amount, 2),
                    'energy': concentrates.energy or 0,
                    'protein': concentrates.protein or 0
                }
                recommendations.append(f"Концентраты ({concentrates.name}): {conc_amount:.2f} кг/день")
            
            # Ищем добавки
            supplements = feeds.filter(type='добавка').first()
            if supplements:
                supp_amount = total_dmi * 0.05
                composition['supplements'] = {
                    'name': supplements.name,
                    'amount_kg': round(supp_amount, 2),
                    'energy': supplements.energy or 0,
                    'protein': supplements.protein or 0
                }
                recommendations.append(f"Добавки ({supplements.name}): {supp_amount:.2f} кг/день")
        
        # Создаем запись рациона
        ration = Ration.objects.create(
            animal=animal,
            total_dmi=round(total_dmi, 2),
            energy_content=round(total_dmi * 8.5, 2),
            calculation_date=timezone.now(),
            composition=composition
        )
        
        recommendations.insert(0, f"Общий сухой корм: {total_dmi:.2f} кг/день")
        
        return {
            'success': True,
            'ration_id': ration.ration_id,
            'total_dmi': round(total_dmi, 2),
            'composition': composition,
            'recommendations': recommendations,
            'message': f"Рацион для {animal.name} рассчитан успешно"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def run_ml_analysis(video):
    """Запуск ML анализа видео (заглушка, потом заменим на реальный)"""
    try:
        # Здесь будет интеграция с реальной ML моделью
        # Пока используем случайные данные для демонстрации
        
        is_lame = random.random() > 0.7  # 30% chance
        
        analysis = Analysis.objects.create(
            video=video,
            analysis_date=timezone.now(),
            is_lame=is_lame,
            lameness_probability=round(random.uniform(0.1, 0.9), 2),
            lameness_confidence=round(random.uniform(0.6, 0.95), 2),
            diagnosis="Подозрение на хромоту передней левой конечности" if is_lame else "Норма",
            diagnosis_note="Рекомендуется наблюдение у ветеринара" if is_lame else "Хромота не обнаружена",
            confidence_score=round(random.uniform(0.7, 0.95), 2)
        )
        
        # Обновляем статус видео
        video.analysis_status = 'analyzed'
        video.save()
        
        return {
            'success': True,
            'analysis_id': analysis.analysis_id,
            'is_lame': analysis.is_lame,
            'diagnosis': analysis.diagnosis,
            'confidence': analysis.confidence_score
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
