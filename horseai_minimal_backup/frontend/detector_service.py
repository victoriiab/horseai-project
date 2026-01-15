"""
Сервис для работы с детектором хромоты
"""

import os
import json
import tempfile
import subprocess
import time
from pathlib import Path
import re

class DetectorService:
    """Сервис для работы с детектором хромоты"""
    
    def __init__(self):
        self.detector_path = "/home/ais/shared/horseAI/final_real_detector_correct.py"
        print(f"✅ DetectorService инициализирован")
        print(f"   Детектор: {self.detector_path}")
    
    def analyze_video(self, video_path, animal_id=None):
        """
        Анализирует видео и возвращает результат
        """
        print(f"🔍 Анализируем видео: {video_path}")
        
        video_path = Path(video_path)
        if not video_path.exists():
            return {
                'success': False,
                'error': f'Файл не найден: {video_path}'
            }
        
        # Создаем временную директорию
        with tempfile.TemporaryDirectory() as tmpdir:
            print(f"📁 Временная директория: {tmpdir}")
            
            # Готовим команду
            cmd = [
                "python3", self.detector_path,
                "--video", str(video_path),
                "--output", tmpdir
            ]
            
            if animal_id:
                cmd.extend(["--video-id", str(animal_id)])
            
            print(f"🔄 Команда: {' '.join(cmd)}")
            
            try:
                # Запускаем детектор
                start_time = time.time()
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 минут максимум
                )
                
                elapsed = time.time() - start_time
                print(f"✅ Детектор завершился за {elapsed:.1f} сек")
                print(f"   Код возврата: {result.returncode}")
                
                # Парсим JSON результат из stdout
                json_result = self._extract_json(result.stdout)
                
                if json_result:
                    print(f"📊 Найден JSON результат")
                    return {
                        'success': True,
                        'data': json_result,
                        'processing_time': elapsed,
                        'stdout': result.stdout[:500],
                        'detector': 'real'
                    }
                else:
                    print(f"⚠️  JSON не найден в выводе")
                    return {
                        'success': result.returncode == 0,
                        'stdout': result.stdout[:1000],
                        'stderr': result.stderr[:500] if result.stderr else '',
                        'processing_time': elapsed,
                        'detector': 'real'
                    }
                    
            except subprocess.TimeoutExpired:
                print("⏰ Таймаут! Детектор работал больше 10 минут")
                return {'success': False, 'error': 'Таймаут анализа (10 минут)'}
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                import traceback
                traceback.print_exc()
                return {'success': False, 'error': str(e)}
    
    def _extract_json(self, stdout):
        """Извлекает JSON из вывода детектора"""
        try:
            # Ищем JSON между маркерами ===JSON_START=== и ===JSON_END===
            pattern = r'===JSON_START===\s*(.*?)\s*===JSON_END==='
            match = re.search(pattern, stdout, re.DOTALL)
            
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
            
            # Ищем любой JSON в выводе
            json_pattern = r'\{.*\}'
            matches = list(re.finditer(json_pattern, stdout, re.DOTALL))
            
            for match in matches:
                try:
                    return json.loads(match.group())
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"⚠️  Ошибка парсинга JSON: {e}")
            return None
    
    def test(self):
        """Тестирует соединение с детектором"""
        print("🧪 Тестируем детектор...")
        
        # Просто проверяем что файл существует и можно импортировать
        if not os.path.exists(self.detector_path):
            return {'success': False, 'error': 'Файл детектора не найден'}
        
        # Пробуем запустить с --help
        try:
            cmd = ["python3", self.detector_path, "--help"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': 'Детектор доступен',
                    'help': result.stdout[:200]
                }
            else:
                return {
                    'success': False,
                    'error': f'Код возврата: {result.returncode}',
                    'stderr': result.stderr[:200]
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Создаем глобальный экземпляр
detector_service = DetectorService()

# Тест
if __name__ == "__main__":
    print("=== ТЕСТ DetectorService ===")
    
    # Тестируем подключение
    test_result = detector_service.test()
    print(f"📋 Тест подключения: {test_result}")
    
    # Тестируем на рабочем видео
    test_video = "/home/ais/shared/horseAI/horseai_project/api/uploads/167ba225_healthy_20_mirrored_hhFES5M.mp4"
    
    if os.path.exists(test_video):
        print(f"\n📹 Тестовое видео: {test_video}")
        result = detector_service.analyze_video(test_video)
        print(f"\n📊 Результат анализа: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}...")
    else:
        print("❌ Тестовое видео не найдено")
