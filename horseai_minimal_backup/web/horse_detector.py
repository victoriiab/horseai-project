import numpy as np
import os
from scipy.signal import savgol_filter
from typing import Dict, Optional
import warnings
import pandas as pd
import joblib
from pathlib import Path
from typing import Tuple, Optional
import deeplabcut
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
import warnings
import time
warnings.filterwarnings('ignore')

import sys

current_dir = Path(__file__).parent
project_root = os.path.dirname(current_dir)
parent_dir = os.path.dirname(current_dir)
sys.path.append(str(parent_dir))


def extract_features(df: pd.DataFrame) -> Optional[Dict[str, float]]:
    """Извлечь 12 признаков из DataFrame"""
    try:
        # Инициализация маппинга
        paw_mapping = { 
            'front_left': None, 'front_right': None,
            'back_left': None, 'back_right': None
        }
        
        # Поиск столбцов
        for col in df.columns:
            if len(col) < 4:
                continue
                
            part_name = str(col[2]) if len(col) > 2 else ''
            coord = str(col[3]) if len(col) > 3 else ''
            
            if coord == 'y':
                if 'front_left_paw' in part_name:
                    paw_mapping['front_left'] = col
                elif 'front_right_paw' in part_name:
                    paw_mapping['front_right'] = col
                elif 'back_left_paw' in part_name:
                    paw_mapping['back_left'] = col
                elif 'back_right_paw' in part_name:
                    paw_mapping['back_right'] = col
        
        # Проверка
        if not all(paw_mapping.values()):
            return None
        
        # Извлечение сигналов
        signals_raw = {}
        for paw, col in paw_mapping.items():
            signals_raw[paw] = -df[col].values
        
        # Фильтрация
        common_mask = np.ones(len(df), dtype=bool)
        for y_values in signals_raw.values():
            finite_mask = np.isfinite(y_values)
            if np.sum(finite_mask) < 10:
                return None
            common_mask = common_mask & finite_mask
        
        common_indices = np.where(common_mask)[0]
        if len(common_indices) < 20:
            return None
        
        # Нормализация и сглаживание
        signals = {}
        scale_factor = 1.0
        
        for paw, y_values in signals_raw.items():
            signal = y_values[common_indices]
            signal_centered = signal - np.mean(signal)
            signals[paw] = signal_centered / scale_factor
        
        # Сглаживание
        signals_smoothed = {}
        for paw, signal in signals.items():
            try:
                window_length = min(11, len(signal) if len(signal) % 2 == 1 else len(signal) - 1)
                if window_length < 5:
                    window_length = 5
                smoothed = savgol_filter(signal, window_length=window_length, polyorder=3)
                signals_smoothed[paw] = smoothed
            except:
                signals_smoothed[paw] = signal
        
        # Вычисление признаков
        features = _compute_12_features(signals_smoothed)
        
        return features if features else None
        
    except Exception as e:
        warnings.warn(f"Ошибка при извлечении признаков: {str(e)}")
        return None

def _compute_12_features(signals: Dict[str, np.ndarray]) -> Dict[str, float]:
    """Вычислить 12 признаков"""
    def calculate_amplitude(signal, num_segments=5):
        if len(signal) == 0:
            return 0.0
        
        segment_size = len(signal) // num_segments
        segment_amplitudes = []
        
        for i in range(num_segments):
            start_idx = i * segment_size
            end_idx = start_idx + segment_size
            if i == num_segments - 1:
                end_idx = len(signal)
                
            segment = signal[start_idx:end_idx]
            if len(segment) > 0:
                q85, q15 = np.percentile(segment, [85, 15])
                segment_amp = q85 - q15
                
                if segment_amp > 0 and segment_amp < np.ptp(signal) * 0.8:
                    segment_amplitudes.append(segment_amp)
        
        if not segment_amplitudes:
            q85, q15 = np.percentile(signal, [85, 15])
            return q85 - q15
        
        return np.median(segment_amplitudes)
    
    # Расчет амплитуд
    amp_fl = calculate_amplitude(signals['front_left'])
    amp_fr = calculate_amplitude(signals['front_right'])
    amp_bl = calculate_amplitude(signals['back_left'])
    amp_br = calculate_amplitude(signals['back_right'])
    
    features = {}
    
    # 12 признаков
    features['front_asymmetry'] = abs(amp_fl - amp_fr) / (amp_fl + amp_fr + 1e-10)
    features['back_asymmetry'] = abs(amp_bl - amp_br) / (amp_bl + amp_br + 1e-10)
    features['min_amplitude'] = min(amp_fl, amp_fr, amp_bl, amp_br)
    
    front_avg = (amp_fl + amp_fr) / 2
    back_avg = (amp_bl + amp_br) / 2

    features['back_front_ratio'] = back_avg / (front_avg + 1e-10)

    features['front_left_var'] = np.std(signals['front_left'])
    features['front_right_var'] = np.std(signals['front_right'])
    
    def correlation(s1, s2):
        if np.std(s1) < 1e-10 or np.std(s2) < 1e-10:
            return 0.0
        return np.corrcoef(s1, s2)[0, 1]
    
    features['front_sync'] = correlation(signals['front_left'], signals['front_right'])
    features['back_sync'] = correlation(signals['back_left'], signals['back_right'])
    features['diagonal_sync'] = correlation(signals['front_left'], signals['back_right'])
    
    vel_fl = np.mean(np.abs(np.diff(signals['front_left'])))
    vel_fr = np.mean(np.abs(np.diff(signals['front_right'])))
    features['front_velocity'] = (vel_fl + vel_fr) / 2
    
    acc_fl = np.diff(np.diff(signals['front_left']))
    features['front_jerk'] = np.std(acc_fl) if len(acc_fl) > 0 else 0
    
    features['total_rom'] = (amp_fl + amp_fr + amp_bl + amp_br) / 4
    
    # Проверка
    for key, value in features.items():
        if not np.isfinite(value):
            features[key] = 0.0
    
    return features
    
class HorseLamenessDetector:
    def __init__(self):
        current_dir = Path(__file__).parent
        self.project_root = Path("/home/ais/shared/horseAI")
        self.ml_model_path = Path("/home/ais/shared/horseAI/models/trained/model.pkl")
        self.output_dir = Path("/home/ais/shared/horseAI/media/results")    
        
        print("Детектор хромоты лошадей")
        print(f"Проект: {self.project_root}")
        print(f"Модель: {self.ml_model_path}")
        print(f"Выход: {self.output_dir}")
        print()
        
        # Создаем директорию если нет
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_ml_model()
    
    def _load_ml_model(self):
        print("Загрузка модели...")
        
        try:
            model_data = joblib.load(self.ml_model_path)
            self.scaler = model_data['scaler']
            self.hybrid_model = model_data['hybrid_model']
            self.key_thresholds = {
                'threshold_rf': model_data.get('threshold_rf', 0.5),
                'threshold_nn': model_data.get('threshold_nn', 0.5),
                'threshold_hybrid': model_data.get('threshold_hybrid', 0.5)
            }
            self.feature_thresholds = model_data.get('feature_thresholds', {})
            print(f"Загружено порогов признаков: {len(self.feature_thresholds)}")
            
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            raise

    def _extract_signals(self, df):
        """Извлечь сигналы копыт для визуализации"""
        try:
            paw_mapping = { 
                'front_left': None, 'front_right': None,
                'back_left': None, 'back_right': None
            }
            
            for col in df.columns:
                if len(col) < 4:
                    continue
                    
                part_name = str(col[2]) if len(col) > 2 else ''
                coord = str(col[3]) if len(col) > 3 else ''
                
                if coord == 'y':
                    if 'front_left_paw' in part_name:
                        paw_mapping['front_left'] = col
                    elif 'front_right_paw' in part_name:
                        paw_mapping['front_right'] = col
                    elif 'back_left_paw' in part_name:
                        paw_mapping['back_left'] = col
                    elif 'back_right_paw' in part_name:
                        paw_mapping['back_right'] = col
            
            signals_raw = {} 
            for paw, col in paw_mapping.items(): 
                if col and col in df.columns:
                    signals_raw[paw] = -df[col].values
                else:
                    signals_raw[paw] = np.zeros(len(df))
            
            # Фильтрация NaN
            signals = {}
            for paw, signal in signals_raw.items():
                finite_mask = np.isfinite(signal)
                if np.sum(finite_mask) > 0:
                    signals[paw] = signal[finite_mask]
                else:
                    signals[paw] = np.array([0])
            
            return signals
            
        except Exception as e:
            print(f"Ошибка при извлечении сигналов: {e}")
            return {
                'front_left': np.array([0]),
                'front_right': np.array([0]),
                'back_left': np.array([0]),
                'back_right': np.array([0])
            }


    def analyze_video_superanimal(self, video_path: Path) -> Tuple[Optional[Path], Optional[Path]]:
        print(f"Анализ видео: {os.path.basename(video_path)}")
        
        try:
            print("Разметка ключевых точек...")
            
            deeplabcut.video_inference_superanimal(
                videos=[str(video_path)],
                superanimal_name='superanimal_quadruped',
                model_name='hrnet_w32',
                detector_name='ssdlite',
                videotype=os.path.splitext(video_path)[1][1:],
                dest_folder=str(self.output_dir),
                video_adapt=False,
                pcutoff=0.1,
                max_individuals=1 
            )
            
            video_stem = os.path.splitext(os.path.basename(video_path))[0]
            h5_files = list(self.output_dir.glob(f"*{video_stem}*.h5"))
            
            if not h5_files:
                raise FileNotFoundError(f"H5 файл не найден для {video_stem}")
            
            h5_file = h5_files[0]
            print(f"Данные поз: {os.path.basename(h5_file)}")
            
            labeled_video = None
            
            for attempt in range(3):
                labeled_videos = list(self.output_dir.glob(f"*{video_stem}*labeled*.mp4"))
                if not labeled_videos:
                    labeled_videos = list(self.output_dir.glob(f"*{video_stem}*_sk.mp4"))
                
                if labeled_videos:
                    labeled_video = labeled_videos[0]
                    print(f"Видео с разметкой: {os.path.basename(labeled_video)}")
                    break
                
                if attempt < 2:
                    time.sleep(1)
            
            if not labeled_video:
                print("Видео с разметкой не создано")
            
            return h5_file, labeled_video
            
        except Exception as e:
            print(f"Ошибка DLC: {e}")
            raise
    
    def predict_lameness(self, features: dict) -> dict:
        print("Предсказание хромоты...")
        
        if features is None:
            raise ValueError("Признаки не извлечены")
        
        try:
            feature_names = [
                'front_asymmetry', 'back_asymmetry', 'min_amplitude',
                'back_front_ratio', 'front_left_var', 'front_right_var',
                'front_sync', 'back_sync', 'diagonal_sync',
                'front_velocity', 'front_jerk', 'total_rom'
            ]
            
            X = np.array([[features[name] for name in feature_names]])
            X_scaled = self.scaler.transform(X)

            rf_proba = self.hybrid_model.rf_model.predict_proba(X_scaled)[:, 1]
            nn_proba = self.hybrid_model.nn_model.predict(X_scaled).flatten()
            
            hybrid_proba = self.hybrid_model.predict_proba(
                X_scaled, rf_proba=rf_proba, nn_proba=nn_proba
            )[0]
            
            print(f"RF вероятность: {rf_proba[0]:.3f}")
            print(f"NN вероятность: {nn_proba[0]:.3f}")
            print(f"Гибридная вероятность: {hybrid_proba:.3f}")
            
            hybrid_threshold = self.key_thresholds.get('threshold_hybrid', 0.5)
            print(f"Используем обученный порог для гибрида: {hybrid_threshold:.3f}")
            
            pred = hybrid_proba >= hybrid_threshold
            
            max_distance = max(hybrid_threshold, 1 - hybrid_threshold)
            distance_from_threshold = abs(hybrid_proba - hybrid_threshold)
            confidence = min(100, (distance_from_threshold / max_distance) * 100)
            
            if confidence >= 70:
                if pred:
                    diagnosis = "Хромая"
                    diagnosis_note = "(высокая уверенность)"
                else:
                    diagnosis = "Здоровая" 
                    diagnosis_note = "(высокая уверенность)"
            elif confidence >= 50:
                if pred:
                    diagnosis = "Вероятно хромая"
                    diagnosis_note = "(рекомендуется осмотр)"
                else:
                    diagnosis = "Вероятно здоровая"
                    diagnosis_note = "(рекомендуется наблюдение)"
            else:
                diagnosis = "Неопределенный результат"
                diagnosis_note = "(низкая уверенность)"
            
            result = {
                'is_lame': bool(pred),
                'lameness_probability': round(float(hybrid_proba) * 100, 2),
                'confidence': round(float(confidence), 2),
                'diagnosis': diagnosis,
                'diagnosis_note': diagnosis_note,
                'features': features,
                'threshold_used': round(float(hybrid_threshold), 4)
            }
            
            print(f"Вероятность хромоты: {result['lameness_probability']:.1f}%")
            print(f"Порог классификации: {result['threshold_used']:.3f}")
            print(f"Диагноз: {diagnosis} {diagnosis_note}")
            print(f"Уверенность: {result['confidence']:.1f}%")
            
            return result
            
        except Exception as e:
            print(f"Ошибка предсказания: {e}")
            raise

    def _save_result_to_file(self, result_file: Path, video_name: str, result: dict, 
                            h5_file: Path, labeled_video: Optional[Path]):
        
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write("Отчет об анализе лошади\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Анализируемое видео: {video_name}\n")
            f.write(f"Дата анализа: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"Диагноз: {result['diagnosis']}\n")
            f.write(f"Примечание: {result['diagnosis_note']}\n\n")
            
            f.write("Показатели\n")
            f.write("-" * 50 + "\n")
            f.write(f"Вероятность хромоты: {result['lameness_probability']:.1f}%\n")
            f.write(f"Уровень уверенности анализа: {result['confidence']:.1f}%\n")
            
            if result['confidence'] >= 70:
                f.write("Уровень уверенности: высокий\n")
            elif result['confidence'] >= 50:
                f.write("Уровень уверенности: средний\n")
            else:
                f.write("Уровень уверенности: низкий\n")
            f.write("\n")
            
            f.write("Биомеханические характеристики\n")
            f.write("-" * 50 + "\n")
            
            features = result['features']
            
            f.write("Показатели асимметрии:\n")
            f.write(f"    Асимметрия передних конечностей: {features['front_asymmetry']:.4f}\n")
            f.write(f"    Асимметрия задних конечностей:   {features['back_asymmetry']:.4f}\n\n")
            
            f.write("Показатели синхронности:\n")
            f.write(f"    Синхронность передних конечностей: {features['front_sync']:.4f}\n")
            f.write(f"    Синхронность задних конечностей:   {features['back_sync']:.4f}\n")
            f.write(f"    Диагональная синхронность:         {features['diagonal_sync']:.4f}\n\n")
            
            f.write("Динамические параметры:\n")
            f.write(f"    Скорость движения:     {features['front_velocity']:.4f}\n")
            f.write(f"    Общая амплитуда:       {features['total_rom']:.4f}\n")
            f.write(f"    Отношение нагрузки:    {features['back_front_ratio']:.4f}\n")
            f.write(f"    Минимальная амплитуда: {features['min_amplitude']:.4f}\n\n")
            
            f.write("Анализ отклонений от нормы\n")
            f.write("-" * 50 + "\n")
            
            front_asym_info = self.feature_thresholds.get('front_asymmetry', {'q25': 0.05, 'q75': 0.23})
            back_asym_info = self.feature_thresholds.get('back_asymmetry', {'q25': 0.08, 'q75': 0.34})
            front_sync_info = self.feature_thresholds.get('front_sync', {'q25': 0.42, 'q75': 0.90})
            back_front_info = self.feature_thresholds.get('back_front_ratio', {'q25': 0.83, 'q75': 1.37})

            f.write(f"Асимметрия передних: {features['front_asymmetry']:.4f} (норма: {front_asym_info['q25']:.3f}-{front_asym_info['q75']:.3f})\n")
            f.write(f"Асимметрия задних:   {features['back_asymmetry']:.4f} (норма: {back_asym_info['q25']:.3f}-{back_asym_info['q75']:.3f})\n")
            f.write(f"Синхронность передних: {features['front_sync']:.4f} (норма: {front_sync_info['q25']:.3f}-{front_sync_info['q75']:.3f})\n")
            f.write(f"Отношение нагрузки:   {features['back_front_ratio']:.4f} (норма: {back_front_info['q25']:.3f}-{back_front_info['q75']:.3f})\n\n")
            
            f.write("Интерпретация результатов\n")
            f.write("-" * 50 + "\n")
            interpretation = self._get_interpretation(features, result['is_lame'])
            f.write(interpretation + "\n\n")
            
            f.write("Рекомендации\n")
            f.write("-" * 50 + "\n")
            if result['confidence'] >= 70:
                if result['is_lame']:
                    f.write("Срочно обратиться к ветеринарному врачу\n")
                    f.write("Провести дополнительную диагностику\n")
                    f.write("Ограничить физические нагрузки\n")
                else:
                    f.write("Продолжать регулярные наблюдения\n")
                    f.write("Биомеханические показатели в норме\n")
            elif result['confidence'] >= 50:
                f.write("Рекомендуется показать лошадь ветеринарному специалисту\n")
            else:
                f.write("Требуется повторный анализ видео\n")
                f.write("Возможно, видео недостаточно качественное\n")
                f.write("Рекомендуется консультация специалиста\n")
            f.write("\n")
            
            f.write("Техническая информация\n")
            f.write("-" * 50 + "\n")
            f.write(f"Файл данных поз: {os.path.basename(h5_file)}\n")
            if labeled_video:
                f.write(f"Видео с разметкой: {os.path.basename(labeled_video)}\n")
            f.write(f"Уверенность предсказания: {result['confidence']:.1f}%\n")
            
            f.write("\nРасположение файлов\n")
            f.write("-" * 50 + "\n")
            f.write(f"H5 файл с данными поз: {os.path.basename(h5_file)}\n")
            if labeled_video:
                f.write(f"Видео с разметкой: {os.path.basename(labeled_video)}\n")
            f.write(f"Все файлы находятся в: {self.output_dir}\n")
        
        print(f"Текстовый отчет: results/{os.path.basename(result_file)}")

    def _get_interpretation(self, features: dict, is_lame: bool) -> str:
        interpretations = []   
        
        front_asym_info = self.feature_thresholds.get('front_asymmetry', {'q25': 0.05, 'q75': 0.23})
        back_asym_info = self.feature_thresholds.get('back_asymmetry', {'q25': 0.08, 'q75': 0.34})
        front_sync_info = self.feature_thresholds.get('front_sync', {'q25': 0.42, 'q75': 0.90})
        back_front_info = self.feature_thresholds.get('back_front_ratio', {'q25': 0.83, 'q75': 1.37})
        
        front_asym_q25 = front_asym_info.get('q25', 0.05)
        front_asym_q75 = front_asym_info.get('q75', 0.23)
        back_asym_q25 = back_asym_info.get('q25', 0.08)
        back_asym_q75 = back_asym_info.get('q75', 0.34)
        front_sync_q25 = front_sync_info.get('q25', 0.42)
        front_sync_q75 = front_sync_info.get('q75', 0.90)
        back_front_q25 = back_front_info.get('q25', 0.83)
        back_front_q75 = back_front_info.get('q75', 1.37)
        
        if features['front_asymmetry'] > front_asym_q75:
            interpretations.append(f"Выраженная асимметрия передних конечностей (>{front_asym_q75:.3f})")
        elif features['front_asymmetry'] > front_asym_q25:
            interpretations.append(f"Умеренная асимметрия передних конечностей (>{front_asym_q25:.3f})")
        else:
            interpretations.append(f"Незначительная асимметрия передних конечностей (<={front_asym_q25:.3f})")
        
        if features['back_asymmetry'] > back_asym_q75:
            interpretations.append(f"Выраженная асимметрия задних конечностей (>{back_asym_q75:.3f})")
        elif features['back_asymmetry'] > back_asym_q25:
            interpretations.append(f"Умеренная асимметрия задних конечностей (>{back_asym_q25:.3f})")
        else:
            interpretations.append(f"Незначительная асимметрия задних конечностей (<={back_asym_q25:.3f})")
        
        if features['front_sync'] < front_sync_q25:
            interpretations.append(f"Нарушена синхронность передних конечностей (<{front_sync_q25:.3f})")
        else:
            interpretations.append(f"Синхронность передних конечностей в норме (>={front_sync_q25:.3f})")
        
        if features['back_front_ratio'] < back_front_q25:
            interpretations.append(f"Снижена нагрузка на задние конечности (<{back_front_q25:.3f})")
        elif features['back_front_ratio'] > back_front_q75:
            interpretations.append(f"Повышена нагрузка на задние конечности (>{back_front_q75:.3f})")
        else:
            interpretations.append(f"Распределение нагрузки сбалансировано ({back_front_q25:.3f}-{back_front_q75:.3f})")
        
        if is_lame:
            interpretations.append("\nРекомендуется осмотр ветеринарным врачом")
        else:
            interpretations.append("\nБиомеханические показатели в пределах нормы")
        
        return '\n'.join(interpretations)
    
    
    def save_gait_analysis_report(self, result_file: Path, result: dict):
        print("Создание графического отчета анализа походки...")
        
        if not hasattr(self, 'last_signals'):
            print("Нет данных для визуализации")
            return
        
        signals = self.last_signals
        
        try:
            fig = plt.figure(figsize=(20, 16))
            fig.suptitle(f'Анализ походки лошади\nДиагноз: {result["diagnosis"]}', 
                        fontsize=14, fontweight='bold', y=0.98)
            
            # 1. График сигналов
            ax1 = plt.subplot2grid((3, 3), (0, 0), colspan=2)
            colors = {'front_left': 'red', 'front_right': 'blue', 
                    'back_left': 'green', 'back_right': 'orange'}
            labels = {'front_left': 'Переднее левое', 'front_right': 'Переднее правое',
                    'back_left': 'Заднее левое', 'back_right': 'Заднее правое'}
            
            for paw, signal in signals.items():
                if len(signal) > 0:
                    frames = np.arange(len(signal))
                    ax1.plot(frames, signal, color=colors[paw], label=labels[paw], linewidth=1.5, alpha=0.8)
            
            ax1.set_title('Движение копыт в вертикальной плоскости', fontweight='bold')
            ax1.set_xlabel('Кадры видео')
            ax1.set_ylabel('Амплитуда')
            ax1.legend(loc='upper right', fontsize=9)
            ax1.grid(True, alpha=0.3)
            
            # 2. Столбчатая диаграмма амплитуд
            ax2 = plt.subplot2grid((3, 3), (0, 2))
            paws = ['Перед\nлев', 'Перед\nправ', 'Зад\nлев', 'Зад\nправ']
            
            if all(len(signal) > 0 for signal in signals.values()):
                amplitudes = [np.ptp(signals['front_left']), 
                            np.ptp(signals['front_right']),
                            np.ptp(signals['back_left']), 
                            np.ptp(signals['back_right'])]
            else:
                amplitudes = [0, 0, 0, 0]
            
            bars = ax2.bar(paws, amplitudes, color=['red', 'blue', 'green', 'orange'], alpha=0.7)
            ax2.set_title('Амплитуда движения копыт', fontweight='bold')
            ax2.set_ylabel('Амплитуда')
            ax2.grid(True, alpha=0.3, axis='y')
            
            for bar, amp in zip(bars, amplitudes):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'{amp:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
            
            # 3. ВСЕ 12 признаков
            ax3 = plt.subplot2grid((3, 3), (1, 0), colspan=3)
            features = result['features']
            
            # Все 12 признаков
            all_metrics = {
                '1. Асимметрия передних': features['front_asymmetry'],
                '2. Асимметрия задних': features['back_asymmetry'],
                '3. Синхронность передних': features['front_sync'],
                '4. Синхронность задних': features['back_sync'],
                '5. Диаг. синхронность': features['diagonal_sync'],
                '6. Отношение нагрузки': features['back_front_ratio'],
                '7. Мин. амплитуда': features['min_amplitude'],
                '8. Общая амплитуда': features['total_rom'],
                '9. Дисперсия перед.лев': features['front_left_var'],
                '10. Дисперсия перед.прав': features['front_right_var'],
                '11. Скорость передних': features['front_velocity'],
                '12. Рывок передних': features['front_jerk']
            }
            
            # Цвета в зависимости от значений
            colors_bars = []
            for name, value in all_metrics.items():
                if 'Асимметрия' in name:
                    colors_bars.append('red' if value > 0.3 else 'orange' if value > 0.15 else 'green')
                elif 'Синхронность' in name:
                    colors_bars.append('green' if value > 0.6 else 'orange' if value > 0.3 else 'red')
                elif 'Нагрузка' in name:
                    colors_bars.append('green' if 0.9 <= value <= 1.3 else 'orange' if 0.7 <= value <= 1.5 else 'red')
                elif 'Амплитуда' in name:
                    colors_bars.append('green' if value > 0.02 else 'orange' if value > 0.01 else 'red')
                elif 'Дисперсия' in name:
                    colors_bars.append('blue')
                elif 'Скорость' in name or 'Рывок' in name:
                    colors_bars.append('purple')
                else:
                    colors_bars.append('gray')
            
            x_pos = np.arange(len(all_metrics))
            bars = ax3.bar(x_pos, list(all_metrics.values()), color=colors_bars, alpha=0.7, width=0.8)
            ax3.set_title('Все 12 биомеханических признаков', fontweight='bold', pad=20)
            ax3.set_ylabel('Значение')
            ax3.set_xticks(x_pos)
            ax3.set_xticklabels(all_metrics.keys(), rotation=45, ha='right', fontsize=9)
            ax3.grid(True, alpha=0.3, axis='y')
            
            # Добавляем значения на столбцы
            for bar, value in zip(bars, all_metrics.values()):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2, height + 0.01 * max(all_metrics.values()), 
                        f'{value:.4f}', ha='center', va='bottom', fontsize=7, fontweight='bold')
            
            # 4. Информационная панель с уверенностью (ИСПРАВЛЕНА РАМОЧКА)
            ax4 = plt.subplot2grid((3, 3), (2, 0), colspan=2)
            ax4.axis('off')
            
            diagnosis_text = (
                f"Диагностическая информация\n\n"
                f"Вероятность хромоты: {result['lameness_probability']:.1f}%\n"
                f"Уверенность анализа: {result['confidence']:.1f}%\n"
                f"Диагноз: {result['diagnosis']}\n"
                f"Примечание: {result['diagnosis_note']}\n\n"
                f"Порог классификации: {result['threshold_used']:.3f}"
            )
            
            # Цвет фона в зависимости от диагноза
            if result['is_lame']:
                if result['confidence'] >= 70:
                    bg_color = 'lightcoral'
                    border_color = 'red'
                else:
                    bg_color = 'lightyellow'
                    border_color = 'orange'
            else:
                if result['confidence'] >= 70:
                    bg_color = 'lightgreen'
                    border_color = 'green'
                else:
                    bg_color = 'lightyellow'
                    border_color = 'orange'
            
            # РАМОЧКА НОРМАЛЬНАЯ - не съезжает
            text_box = dict(boxstyle="round,pad=0.5", facecolor=bg_color, 
                        alpha=0.8, edgecolor=border_color, linewidth=3)
            
            ax4.text(0.5, 0.85, diagnosis_text, ha='center', va='center', 
                    fontsize=11, fontweight='bold', transform=ax4.transAxes,
                    bbox=text_box)
            
            # 5. Простой индикатор уверенности
            ax5 = plt.subplot2grid((3, 3), (2, 2))
            ax5.axis('off')
            
            confidence_level = result['confidence'] / 100
            confidence_color = 'green' if result['confidence'] >= 70 else \
                            'orange' if result['confidence'] >= 50 else 'red'
            
            # Круглый индикатор
            circle = plt.Circle((0.5, 0.5), 0.4, color='lightgray', alpha=0.3)
            ax5.add_patch(circle)
            
            # Заполненная часть
            if confidence_level > 0:
                wedge = plt.Circle((0.5, 0.5), 0.4 * confidence_level, 
                                color=confidence_color, alpha=0.8)
                ax5.add_patch(wedge)
            
            ax5.text(0.5, 0.5, f'{result["confidence"]:.1f}%', 
                    ha='center', va='center', fontsize=16, fontweight='bold')
            ax5.text(0.5, 0.2, 'УВЕРЕННОСТЬ', 
                    ha='center', va='center', fontsize=10, fontweight='bold')
            
            # Устанавливаем границы
            ax5.set_xlim(0, 1)
            ax5.set_ylim(0, 1)
            ax5.set_aspect('equal')
            
            plt.tight_layout()
            plt.subplots_adjust(top=0.92, hspace=0.4, wspace=0.3)
            
            plot_path = result_file.with_suffix('.png')
            plt.savefig(plot_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            print(f"Графический отчет сохранен: {os.path.basename(plot_path)}")
            
        except Exception as e:
            print(f"Ошибка при создании графического отчета: {e}")
            import traceback
            traceback.print_exc()
                
    def process(self, video_path: Path):
        print("=" * 70)
        print(f"Анализ: {os.path.basename(video_path)}")
        print("=" * 70)
        
        try:
            results_dir = self.output_dir / "results"
            results_dir.mkdir(exist_ok=True)
            
            h5_file, labeled_video = self.analyze_video_superanimal(video_path)
            
            print(f"H5 файл: {os.path.basename(h5_file)}")
            if labeled_video:
                print(f"Размеченное видео: {os.path.basename(labeled_video)}")
            
            import pandas as pd
            df = pd.read_hdf(h5_file)
            
            features = extract_features(df)
            
            if features is None:
                print("Не удалось извлечь признаки")
                return False
            
            self.last_signals = self._extract_signals(df)
            
            result = self.predict_lameness(features)
            
            result_file = results_dir / f"{os.path.splitext(os.path.basename(video_path))[0]}_result.txt"
            self._save_result_to_file(result_file, os.path.basename(video_path), result, h5_file, labeled_video)
            
            self.save_gait_analysis_report(result_file, result)

            print(f"Видео {os.path.basename(video_path)} обработано успешно.")
            return True
            
        except Exception as e:
            print(f"Ошибка при обработке {os.path.basename(video_path)}: {e}")
            return False
        self.last_result = result  # Сохраняем результат в атрибут класса
        return True
    

    def get_last_result(self):
        return getattr(self, 'last_result', None)    
    
def main():
    print("Запуск детектора хромоты")
    print()
    
    detector = HorseLamenessDetector()
    
    test_videos_dir = detector.project_root / "test" / "test_videos"
    
    if not os.path.exists(test_videos_dir):
        print(f"Папка не найдена: {test_videos_dir}")
        return
    
    video_files = list(test_videos_dir.glob("*.mp4")) + list(test_videos_dir.glob("*.avi"))
    
    if not video_files:
        print(f"Видео не найдены в {test_videos_dir}")
        return
    
    print(f"Найдено {len(video_files)} видео для анализа")
    print()
    
    success_count = 0
    for video_path in video_files:
        print(f"Анализ: {os.path.basename(video_path)}")
        if detector.process(video_path):
            success_count += 1
        print("-" * 50)
    
    print("Анализ завершен")
    print(f"Обработано: {success_count}/{len(video_files)} видео")

if __name__ == "__main__":
    main()
