"""
Views для анализа хромоты лошадей
"""

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import subprocess
import time
import os
from pathlib import Path

@csrf_exempt
def lameness_test_api(request):
    """НАСТОЯЩИЙ тест анализа хромоты - API endpoint"""
    try:
        # Проверяем что детектор существует
        detector_path = Path("/home/ais/shared/horseAI/final_real_detector.py")
        
        if not detector_path.exists():
            return JsonResponse({
                'success': False,
                'error': 'Детектор не найден'
            }, status=404)
        
        # Тестовое видео
        test_video = Path("/home/ais/shared/horseAI/test/test_videos/healthy_20_mirrored_hhFES5M.mp4")
        
        if not test_video.exists():
            return JsonResponse({
                'success': False,
                'error': 'Тестовое видео не найдено'
            }, status=404)
        
        # Запускаем НАСТОЯЩИЙ детектор
        video_id = "real_test_" + str(int(time.time()))[-6:]
        
        cmd = [
            "python",
            str(detector_path),
            video_id,
            str(test_video)
        ]
        
        print(f"🚀 Запускаем НАСТОЯЩИЙ анализ: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(f"✅ Детектор завершился с кодом: {result.returncode}")
        
        # Парсим результат
        import re
        json_match = re.search(r'🎯 JSON результат для API:\s*(\{.*\})', result.stdout, re.DOTALL)
        
        if json_match:
            result_data = json.loads(json_match.group(1))
            return JsonResponse({
                'success': True,
                'message': 'НАСТОЯЩИЙ анализ завершен',
                'result': result_data,
                'stdout_preview': result.stdout[:500] + '...' if len(result.stdout) > 500 else result.stdout
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Не удалось получить результат из вывода',
                'stdout': result.stdout[-1000:],
                'stderr': result.stderr[-500:]
            }, status=500)
            
    except subprocess.TimeoutExpired:
        return JsonResponse({
            'success': False,
            'error': 'Анализ занял слишком много времени (>5 минут)'
        }, status=408)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def lameness_test_page(request):
    """Страница для тестирования НАСТОЯЩЕГО анализа"""
    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Horse AI - НАСТОЯЩИЙ анализ хромоты</title>
        <style>
            body { font-family: Arial; padding: 20px; max-width: 800px; margin: 0 auto; }
            .test-box { background: #f0f9ff; border: 2px solid #4CAF50; padding: 30px; text-align: center; margin: 20px 0; border-radius: 10px; }
            button { background: #4CAF50; color: white; border: none; padding: 15px 30px; margin: 10px; cursor: pointer; font-size: 16px; border-radius: 5px; }
            button:hover { background: #45a049; }
            button:disabled { background: #ccc; cursor: not-allowed; }
            .result { margin-top: 30px; padding: 25px; background: #f9f9f9; border-radius: 10px; border-left: 5px solid #4CAF50; }
            .status { padding: 15px; margin: 15px 0; border-radius: 8px; font-weight: bold; }
            .processing { background: #fff3cd; border: 2px solid #ffeaa7; }
            .success { background: #d4edda; border: 2px solid #c3e6cb; }
            .error { background: #f8d7da; border: 2px solid #f5c6cb; }
            .badge { display: inline-block; padding: 8px 20px; border-radius: 20px; color: white; font-weight: bold; margin: 10px 0; }
            .healthy { background: green; }
            .lame { background: red; }
            table { width: 100%; border-collapse: collapse; margin: 15px 0; }
            td, th { padding: 10px; border-bottom: 1px solid #ddd; text-align: left; }
            th { background: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>🐴 НАСТОЯЩИЙ анализ хромоты лошадей</h1>
        <p>Тестирование реальной ML модели на примере видео</p>
        
        <div class="test-box">
            <h2>Запуск НАСТОЯЩЕГО анализа</h2>
            <p>Будет использована ваша реальная модель <code>/home/ais/shared/horseAI/models/trained/model.pkl</code></p>
            <p>Время анализа: ~2-3 минуты</p>
            <button onclick="runRealTest()" id="testBtn">🚀 Запустить НАСТОЯЩИЙ анализ</button>
            <div id="status" class="status" style="display: none;"></div>
        </div>
        
        <div id="result" class="result" style="display: none;">
            <h3>🎯 Результаты НАСТОЯЩЕГО анализа:</h3>
            <div id="resultContent"></div>
        </div>
        
        <script>
        async function runRealTest() {
            const btn = document.getElementById('testBtn');
            const statusDiv = document.getElementById('status');
            const resultDiv = document.getElementById('result');
            const contentDiv = document.getElementById('resultContent');
            
            btn.disabled = true;
            btn.textContent = '⏳ Анализ выполняется...';
            statusDiv.style.display = 'block';
            statusDiv.className = 'status processing';
            statusDiv.textContent = 'Запускаем НАСТОЯЩИЙ анализ...';
            resultDiv.style.display = 'none';
            
            try {
                const response = await fetch('/lameness-test-api/');
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    statusDiv.className = 'status success';
                    statusDiv.textContent = '✅ НАСТОЯЩИЙ анализ завершен успешно!';
                    
                    showRealResults(data.result);
                    resultDiv.style.display = 'block';
                } else {
                    statusDiv.className = 'status error';
                    statusDiv.textContent = `❌ Ошибка: ${data.error || 'Неизвестная ошибка'}`;
                }
                
            } catch (error) {
                statusDiv.className = 'status error';
                statusDiv.textContent = `❌ Ошибка: ${error.message}`;
            } finally {
                btn.disabled = false;
                btn.textContent = '🚀 Запустить НАСТОЯЩИЙ анализ';
            }
        }
        
        function showRealResults(result) {
            const contentDiv = document.getElementById('resultContent');
            
            if (!result.success) {
                contentDiv.innerHTML = `<div style="color: red;">Ошибка анализа: ${result.error}</div>`;
                return;
            }
            
            const isLame = result.is_lame ? 'ДА' : 'НЕТ';
            const badgeClass = result.is_lame ? 'lame' : 'healthy';
            
            let html = `
                <div class="badge ${badgeClass}">
                    Хромота: ${isLame}
                </div>
                
                <table>
                    <tr><td><strong>Вероятность хромоты:</strong></td><td>${result.lameness_probability}%</td></tr>
                    <tr><td><strong>Уверенность анализа:</strong></td><td>${result.confidence}%</td></tr>
                    <tr><td><strong>Диагноз:</strong></td><td>${result.diagnosis}</td></tr>
                    <tr><td><strong>Примечание:</strong></td><td>${result.diagnosis_note}</td></tr>
                    <tr><td><strong>Время анализа:</strong></td><td>${result.processing_time_seconds} сек</td></tr>
                    <tr><td><strong>Видео:</strong></td><td>${result.video_filename}</td></tr>
                </table>
                
                <h4>📊 Биомеханические признаки (НАСТОЯЩИЕ):</h4>
                <table>
            `;
            
            if (result.features) {
                const featureNames = {
                    'front_asymmetry': 'Асимметрия передних конечностей',
                    'back_asymmetry': 'Асимметрия задних конечностей',
                    'min_amplitude': 'Минимальная амплитуда',
                    'back_front_ratio': 'Отношение нагрузок (зад/перед)',
                    'front_left_var': 'Дисперсия переднего левого',
                    'front_right_var': 'Дисперсия переднего правого',
                    'front_sync': 'Синхронность передних конечностей',
                    'back_sync': 'Синхронность задних конечностей',
                    'diagonal_sync': 'Диагональная синхронность',
                    'front_velocity': 'Скорость передних конечностей',
                    'front_jerk': 'Рывок передних конечностей',
                    'total_rom': 'Общая амплитуда движения'
                };
                
                for (const [key, value] of Object.entries(result.features)) {
                    const displayName = featureNames[key] || key.replace(/_/g, ' ');
                    html += `
                        <tr>
                            <td>${displayName}:</td>
                            <td><code>${typeof value === 'number' ? value.toFixed(6) : value}</code></td>
                        </tr>
                    `;
                }
            }
            
            html += `</table>`;
            
            if (result.model_details) {
                html += `
                    <h4>🧠 Детали модели:</h4>
                    <table>
                        <tr><td>RF вероятность:</td><td>${result.model_details.rf_probability}%</td></tr>
                        <tr><td>NN вероятность:</td><td>${result.model_details.nn_probability}%</td></tr>
                        <tr><td>Использованный порог:</td><td>${result.model_details.threshold_used}</td></tr>
                    </table>
                `;
            }
            
            contentDiv.innerHTML = html;
        }
        </script>
    </body>
    </html>
    '''
    
    return HttpResponse(html_content)
