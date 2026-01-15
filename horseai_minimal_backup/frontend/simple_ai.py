import numpy as np
import logging

logger = logging.getLogger(__name__)

class HorseAIService:
    def __init__(self):
        logger.info("HorseAI сервис инициализирован (демо-режим)")
        self.is_ready = True
    
    def analyze_video_features(self, video_features):
        """Простой анализ для демо"""
        try:
            # Базовая логика на основе признаков
            front_asym = video_features.get('front_asymmetry', 0.1)
            back_asym = video_features.get('back_asymmetry', 0.1)
            
            # Вероятность хромоты
            probability = min(0.9, max(0.1, (front_asym + back_asym) * 2))
            is_lame = probability > 0.5
            
            # Поза
            velocity = video_features.get('front_velocity', 0.2)
            if velocity > 0.15:
                posture = "движение"
            elif velocity < 0.05:
                posture = "лежа" 
            else:
                posture = "стоя"
            
            # Размер
            rom = video_features.get('total_rom', 0.5)
            if rom > 0.6:
                size = "большой"
                weight = 550
            elif rom > 0.4:
                size = "средний"
                weight = 450
            else:
                size = "маленький" 
                weight = 350
            
            return {
                'is_lame': bool(is_lame),
                'lameness_detected': bool(is_lame),
                'lameness_probability': round(probability * 100, 1),
                'posture': posture,
                'size_category': size,
                'estimated_weight': weight,
                'gait_quality': 'норма' if not is_lame else 'хромота',
                'confidence_score': 0.8,
                'features_used': video_features,
                'model_threshold': 50.0
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа: {e}")
            return self._get_fallback_result()
    
    def extract_features_from_data(self, movement_data):
        """Генерация демо-признаков"""
        return {
            'front_asymmetry': np.random.uniform(0.05, 0.3),
            'back_asymmetry': np.random.uniform(0.05, 0.25),
            'min_amplitude': np.random.uniform(0.3, 0.7),
            'back_front_ratio': np.random.uniform(0.8, 1.2),
            'front_left_var': np.random.uniform(0.1, 0.25),
            'front_right_var': np.random.uniform(0.1, 0.25),
            'front_sync': np.random.uniform(0.6, 0.9),
            'back_sync': np.random.uniform(0.6, 0.9),
            'diagonal_sync': np.random.uniform(0.5, 0.8),
            'front_velocity': np.random.uniform(0.1, 0.3),
            'front_jerk': np.random.uniform(0.03, 0.1),
            'total_rom': np.random.uniform(0.4, 0.7)
        }
    
    def _get_fallback_result(self):
        return {
            'is_lame': False,
            'lameness_detected': False,
            'lameness_probability': 15.0,
            'posture': 'стоя',
            'size_category': 'средний',
            'estimated_weight': 450.0,
            'gait_quality': 'норма',
            'confidence_score': 0.5,
            'features_used': {},
            'model_threshold': 50.0
        }

# Глобальный экземпляр
ai_service = HorseAIService()
