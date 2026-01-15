"""
ПРОСТОЙ И РАБОЧИЙ обработчик видео
"""
import os
import uuid
import json
import threading
import time
from datetime import datetime
from pathlib import Path
import subprocess
import shutil

class VideoProcessor:
    def __init__(self):
        self.media_root = "/home/ais/shared/horseAI/media"
        self.videos_dir = os.path.join(self.media_root, "videos")
        self.results_dir = os.path.join(self.media_root, "analysis_results")
        
        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        
    def save_uploaded_video(self, video_file, user_id, animal_id):
        """Сохраняет загруженное видео"""
        # Создаем уникальное имя файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        original_name = video_file.name.replace(' ', '_')
        filename = f"{timestamp}_{unique_id}_{original_name}"
        
        filepath = os.path.join(self.videos_dir, filename)
        
        # Сохраняем файл
        with open(filepath, 'wb+') as f:
            for chunk in video_file.chunks():
                f.write(chunk)
        
        return {
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'video_url': f'/media/videos/{filename}'
        }
    
    def analyze_video(self, video_path, video_id, animal_id):
        """Запускает анализ видео в отдельном потоке"""
        def run_analysis():
            try:
                print(f"🚀 Начинаем анализ видео ID {video_id}")
                print(f"📹 Путь: {video_path}")
                
                # Создаем папку для результатов
                output_dir = os.path.join(self.results_dir, f"video_{video_id}")
                os.makedirs(output_dir, exist_ok=True)
                
                # Запускаем детектор
                detector_script = "/home/ais/shared/horseAI/final_real_detector_correct.py"
                
                cmd = [
                    "python3", detector_script,
                    "--video", video_path,
                    "--output", output_dir,
                    "--video-id", str(video_id)
                ]
                
                print(f"▶️  Запуск команды: {' '.join(cmd)}")
                
                # Запускаем процесс с таймаутом
                start_time = time.time()
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 минут таймаут
                )
                
                elapsed = time.time() - start_time
                print(f"⏱️  Анализ занял: {elapsed:.1f} секунд")
                
                # Логируем вывод
                log_file = os.path.join(output_dir, "analysis.log")
                with open(log_file, 'w') as f:
                    f.write(f"=== АНАЛИЗ ВИДЕО ID {video_id} ===\n")
                    f.write(f"Время: {datetime.now()}\n")
                    f.write(f"Длительность: {elapsed:.1f} сек\n")
                    f.write(f"Код возврата: {result.returncode}\n\n")
                    f.write("=== STDOUT ===\n")
                    f.write(result.stdout)
                    f.write("\n=== STDERR ===\n")
                    f.write(result.stderr)
                
                # Обновляем статус в БД
                self.update_analysis_status(video_id, result.returncode == 0, output_dir)
                
            except subprocess.TimeoutExpired:
                print(f"⏰ Таймаут анализа видео {video_id}")
                self.update_analysis_status(video_id, False, "Таймаут анализа")
            except Exception as e:
                print(f"💥 Ошибка анализа видео {video_id}: {e}")
                self.update_analysis_status(video_id, False, str(e))
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()
        
        return {
            'success': True,
            'message': 'Анализ запущен в фоне',
            'video_id': video_id,
            'estimated_time': '3-5 минут'
        }
    
    def update_analysis_status(self, video_id, success, result_info):
        """Обновляет статус анализа в БД"""
        try:
            from web.database.models import Video, Analysis
            from django.utils import timezone
            
            # Находим видео
            video = Video.objects.get(video_id=video_id)
            
            # Обновляем статус видео
            video.analysis_status = 'completed' if success else 'failed'
            video.save()
            
            # Создаем или обновляем запись анализа
            analysis, created = Analysis.objects.update_or_create(
                video=video,
                defaults={
                    'analysis_date': timezone.now(),
                    'is_lame': False,  # По умолчанию
                    'lameness_probability': 0.0,
                    'diagnosis': 'Анализ выполнен' if success else 'Ошибка анализа',
                    'diagnosis_note': str(result_info)[:500]
                }
            )
            
            # Если есть результаты, парсим их
            if success and isinstance(result_info, str) and os.path.exists(result_info):
                self.parse_and_save_results(analysis, result_info)
            
            print(f"✅ Статус анализа {video_id} обновлен: {'успешно' if success else 'ошибка'}")
            
        except Exception as e:
            print(f"⚠️ Ошибка обновления статуса {video_id}: {e}")
    
    def parse_and_save_results(self, analysis, output_dir):
        """Парсит результаты и сохраняет в анализ"""
        try:
            # Ищем файл результатов
            result_files = []
            for ext in ['*.json', '*result*.txt', '*.txt']:
                result_files.extend(Path(output_dir).rglob(ext))
            
            if not result_files:
                print(f"⚠️ Файлы результатов не найдены в {output_dir}")
                return
            
            # Берем первый файл
            result_file = result_files[0]
            
            # Пробуем прочитать JSON
            if result_file.suffix == '.json':
                with open(result_file, 'r') as f:
                    data = json.load(f)
                
                # Обновляем анализ
                if 'is_lame' in data:
                    analysis.is_lame = data['is_lame']
                if 'lameness_probability' in data:
                    analysis.lameness_probability = float(data['lameness_probability'])
                if 'confidence' in data:
                    analysis.confidence_score = float(data['confidence']) / 100.0
                if 'diagnosis' in data:
                    analysis.diagnosis = data['diagnosis'][:500]
                if 'diagnosis_note' in data:
                    analysis.diagnosis_note = data['diagnosis_note'][:500]
                
                analysis.save()
                print(f"✅ Результаты из JSON сохранены для анализа {analysis.analysis_id}")
            
            # Или читаем TXT
            else:
                with open(result_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Простой парсинг
                import re
                
                # Диагноз
                diagnosis_match = re.search(r'Диагноз:\s*(.+)', content)
                if diagnosis_match:
                    analysis.diagnosis = diagnosis_match.group(1).strip()[:500]
                
                # Вероятность
                prob_match = re.search(r'Вероятность[:\s]*([\d.]+)%', content)
                if prob_match:
                    analysis.lameness_probability = float(prob_match.group(1))
                
                # Уверенность
                conf_match = re.search(r'Уверенность[:\s]*([\d.]+)%', content)
                if conf_match:
                    analysis.confidence_score = float(conf_match.group(1)) / 100.0
                
                # Хромота?
                if diagnosis_match:
                    diagnosis_text = diagnosis_match.group(1).lower()
                    analysis.is_lame = any(word in diagnosis_text for word in ['хрома', 'вероятно хрома', 'lame'])
                
                analysis.save()
                print(f"✅ Результаты из TXT сохранены для анализа {analysis.analysis_id}")
                
        except Exception as e:
            print(f"⚠️ Ошибка парсинга результатов: {e}")
    
    def get_analysis_status(self, video_id):
        """Получает статус анализа"""
        try:
            from web.database.models import Video, Analysis
            
            video = Video.objects.get(video_id=video_id)
            analysis = Analysis.objects.filter(video=video).first()
            
            return {
                'video_id': video_id,
                'status': video.analysis_status or 'pending',
                'has_analysis': analysis is not None,
                'analysis_id': analysis.analysis_id if analysis else None,
                'is_lame': analysis.is_lame if analysis else None,
                'diagnosis': analysis.diagnosis if analysis else None,
                'created_at': video.upload_date.strftime('%d.%m.%Y %H:%M') if video.upload_date else None
            }
            
        except Video.DoesNotExist:
            return {'error': 'Видео не найдено'}
        except Exception as e:
            return {'error': str(e)}

# Синглтон
_video_processor = None

def get_video_processor():
    global _video_processor
    if _video_processor is None:
        _video_processor = VideoProcessor()
    return _video_processor
