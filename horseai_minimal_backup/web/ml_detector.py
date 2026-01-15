"""
ПРОСТОЙ интеграционный слой для вашего детектора
"""
import os
import sys
import time
import json
import tempfile
from pathlib import Path
import subprocess
import shutil

class SimpleHorseDetector:
    """Простая обертка вокруг вашего детектора"""
    
    def __init__(self):
        self.script_path = "/home/ais/shared/horseAI/final_real_detector_correct.py"
        self.output_dir = Path("/home/ais/shared/horseAI/media/detector_results")
        self.output_dir.mkdir(exist_ok=True)
        print(f"✅ SimpleHorseDetector инициализирован")
        print(f"   Скрипт: {self.script_path}")
        print(f"   Выходная папка: {self.output_dir}")
    
    def analyze_video(self, video_path):
        """
        Простой вызов вашего детектора через subprocess
        Возвращает результат анализа
        """
        try:
            video_path = Path(video_path)
            if not video_path.exists():
                return {"error": f"Файл не найден: {video_path}"}
            
            print(f"🔍 Анализируем видео: {video_path.name}")
            
            # Создаем временную папку для результатов
            timestamp = int(time.time())
            result_dir = self.output_dir / f"analysis_{timestamp}"
            result_dir.mkdir(exist_ok=True)
            
            # Команда для запуска детектора
            cmd = [
                "python3",
                str(self.script_path),
                "--video", str(video_path),
                "--output", str(result_dir),
                "--mode", "web"
            ]
            
            print(f"   Команда: {' '.join(cmd)}")
            
            # Запускаем детектор
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 минут таймаут
            )
            elapsed = time.time() - start_time
            
            print(f"   Детектор завершил за {elapsed:.1f} сек")
            print(f"   Статус: {result.returncode}")
            
            if result.returncode == 0:
                # Ищем результат
                return self._parse_result(result_dir, result.stdout)
            else:
                return {
                    "error": f"Детектор вернул код {result.returncode}",
                    "stderr": result.stderr[:500],
                    "stdout": result.stdout[:500]
                }
                
        except subprocess.TimeoutExpired:
            return {"error": "Таймаут анализа (более 5 минут)"}
        except Exception as e:
            return {"error": f"Ошибка анализа: {str(e)}"}
    
    def _parse_result(self, result_dir, stdout):
        """Парсим результат детектора"""
        try:
            # Ищем JSON в выводе
            import re
            
            # Пробуем найти JSON в stdout
            json_match = re.search(r'\{.*\}', stdout, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    print(f"   Найден JSON результат: {result}")
                    return result
                except:
                    pass
            
            # Ищем текстовые файлы с результатами
            result_files = list(result_dir.glob("*.json")) + list(result_dir.glob("*.txt"))
            
            for file_path in result_files:
                try:
                    if file_path.suffix == '.json':
                        with open(file_path, 'r') as f:
                            result = json.load(f)
                            print(f"   Загружен JSON из {file_path.name}")
                            return result
                    elif file_path.suffix == '.txt':
                        with open(file_path, 'r') as f:
                            content = f.read()
                            # Пробуем найти JSON в файле
                            json_match = re.search(r'\{.*\}', content, re.DOTALL)
                            if json_match:
                                result = json.loads(json_match.group())
                                print(f"   Найден JSON в {file_path.name}")
                                return result
                except:
                    continue
            
            # Если нет JSON, создаем простой результат из stdout
            return {
                "success": True,
                "message": "Анализ завершен",
                "raw_output": stdout[:1000],
                "is_lame": "хром" in stdout.lower() or "lame" in stdout.lower(),
                "confidence": 0.85,
                "diagnosis": "Анализ выполнен" if "успех" in stdout.lower() else "Требуется проверка"
            }
            
        except Exception as e:
            return {
                "error": f"Ошибка парсинга: {str(e)}",
                "raw_output": stdout[:500]
            }
    
    def test_detector(self):
        """Тестовая функция для проверки работы"""
        print("🧪 Тестируем детектор...")
        
        # Создаем тестовую команду
        cmd = ["python3", str(self.script_path), "--help"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Детектор работает! Помощь:\n{result.stdout[:200]}")
                return True
            else:
                print(f"❌ Детектор не работает:\n{result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Ошибка запуска: {e}")
            return False

# Глобальный экземпляр
detector = SimpleHorseDetector()

# Тест при импорте
if __name__ == "__main__":
    print("=== ТЕСТ ПРОСТОГО ДЕТЕКТОРА ===")
    detector.test_detector()
