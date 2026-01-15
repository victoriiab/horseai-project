"""
Views для загрузки и анализа видео на хромоту - ЧИСТАЯ РАБОЧАЯ ВЕРСИЯ
"""

from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
import json
import subprocess
import time
import os
import uuid
from pathlib import Path
import mimetypes

# Хранилище статусов анализа
analysis_status = {}

def upload_lameness_page(request):
    """Страница для загрузки ВАШЕГО видео"""
    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Horse AI - Анализ хромоты по ВАШЕМУ видео</title>
        <style>
            body { font-family: Arial; padding: 20px; max-width: 900px; margin: 0 auto; }
            .upload-box { background: #e8f5e9; border: 3px dashed #4CAF50; padding: 40px; text-align: center; margin: 20px 0; border-radius: 15px; }
            .file-input { display: none; }
            .upload-label { display: inline-block; background: #4CAF50; color: white; padding: 15px 40px; border-radius: 8px; cursor: pointer; font-size: 16px; }
            button { background: #2196F3; color: white; border: none; padding: 15px 40px; margin: 10px; cursor: pointer; font-size: 16px; border-radius: 8px; }
            button:disabled { background: #ccc; cursor: not-allowed; }
            .status-box { margin: 20px 0; padding: 20px; border-radius: 10px; display: none; }
            .result-box { margin: 30px 0; padding: 30px; background: #f8f9fa; border-radius: 15px; display: none; }
            .badge { display: inline-block; padding: 10px 25px; border-radius: 25px; color: white; font-weight: bold; margin: 15px 0; font-size: 18px; }
            .badge-healthy { background: #4CAF50; }
            .badge-lame { background: #f44336; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; background: white; }
            th, td { padding: 12px 15px; border-bottom: 1px solid #eee; }
            .progress-bar { height: 10px; background: #e0e0e0; border-radius: 5px; margin: 10px 0; }
            .progress-fill { height: 100%; background: #4CAF50; width: 0%; transition: width 0.5s; }
        </style>
    </head>
    <body>
        <h1>🐴 Анализ хромоты лошадей по ВАШЕМУ видео</h1>
        
        <div class="upload-box">
            <h2>📤 Загрузите видео</h2>
            <input type="file" id="videoFile" class="file-input" accept="video/*">
            <label for="videoFile" class="upload-label">📁 Выбрать видео</label>
            <div id="fileInfo" style="display: none; margin-top: 20px;">
                <strong>Выбранный файл:</strong> <span id="fileName"></span>
            </div>
        </div>
        
        <button onclick="startAnalysis()" id="analyzeBtn" disabled>🚀 Запустить анализ</button>
        
        <div id="statusBox" class="status-box">
            <h3>📊 Статус:</h3>
            <div id="statusText">Подготовка...</div>
            <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
            <div id="progressText">0%</div>
        </div>
        
        <div id="resultBox" class="result-box">
            <h2>🎯 Результаты</h2>
            <div id="resultContent"></div>
        </div>
        
        <script>
        let currentVideoId = null;
        
        document.getElementById('videoFile').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            document.getElementById('fileName').textContent = file.name;
            document.getElementById('fileInfo').style.display = 'block';
            document.getElementById('analyzeBtn').disabled = false;
        });
        
        async function startAnalysis() {
            const file = document.getElementById('videoFile').files[0];
            if (!file) return alert('Выберите видео');
            
            document.getElementById('analyzeBtn').disabled = true;
            document.getElementById('statusBox').style.display = 'block';
            document.getElementById('statusText').textContent = 'Загрузка...';
            document.getElementById('progressFill').style.width = '10%';
            
            try {
                const formData = new FormData();
                formData.append('video', file);
                
                const response = await fetch('/api/lameness/upload/', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (!data.success) throw new Error(data.error);
                
                currentVideoId = data.video_id;
                document.getElementById('statusText').textContent = 'Анализ запущен...';
                document.getElementById('progressFill').style.width = '30%';
                
                checkAnalysisStatus();
                
            } catch (error) {
                document.getElementById('statusText').textContent = '❌ Ошибка: ' + error.message;
                document.getElementById('analyzeBtn').disabled = false;
            }
        }
        
        async function checkAnalysisStatus() {
            if (!currentVideoId) return;
            
            try {
                const response = await fetch('/api/lameness/status/' + currentVideoId + '/');
                const data = await response.json();
                
                console.log("Статус ответ:", data);
                
                if (data.status === 'processing') {
                    document.getElementById('statusText').textContent = 'Анализ... (' + (data.elapsed_seconds || 0) + ' сек)';
                    document.getElementById('progressFill').style.width = '60%';
                    setTimeout(checkAnalysisStatus, 3000);
                    
                } else if (data.status === 'completed') {
                    document.getElementById('statusText').textContent = '✅ Анализ завершен!';
                    document.getElementById('progressFill').style.width = '100%';
                    
                    if (data.result) {
                        showResults(data.result);
                    } else {
                        showResults(data);
                    }
                    
                    document.getElementById('analyzeBtn').disabled = false;
                    
                } else if (data.status === 'failed') {
                    document.getElementById('statusText').textContent = '❌ Ошибка: ' + (data.error || '');
                    document.getElementById('analyzeBtn').disabled = false;
                }
                
            } catch (error) {
                console.error(error);
                setTimeout(checkAnalysisStatus, 3000);
            }
        }
        
        function showResults(result) {
            console.log("Показываем результаты:", result);
            
            const resultBox = document.getElementById('resultBox');
            const contentDiv = document.getElementById('resultContent');
            
            if (!result.success) {
                contentDiv.innerHTML = '<div style="color: red;">Ошибка: ' + (result.error || '') + '</div>';
                resultBox.style.display = 'block';
                return;
            }
            
            const isLame = result.is_lame ? 'ДА' : 'НЕТ';
            const badgeClass = result.is_lame ? 'badge-lame' : 'badge-healthy';
            
            let html = `
                <div class="${badgeClass} badge">Хромота: ${isLame}</div>
                <table>
                    <tr><td>Вероятность:</td><td><strong>${result.lameness_probability}%</strong></td></tr>
                    <tr><td>Уверенность:</td><td>${result.confidence}%</td></tr>
                    <tr><td>Диагноз:</td><td>${result.diagnosis}</td></tr>
                    <tr><td>Время анализа:</td><td>${result.processing_time_seconds} сек</td></tr>
                    <tr><td>Видео:</td><td>${result.video_filename}</td></tr>
                </table>
            `;
            
            if (result.annotated_video_path) {
                html += `
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="/api/lameness/download/${result.video_id || currentVideoId}/" 
                           style="display: inline-block; background: #FF9800; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none;">
                            📥 Скачать видео с разметкой
                        </a>
                    </div>
                `;
            }
            
            contentDiv.innerHTML = html;
            resultBox.style.display = 'block';
            resultBox.scrollIntoView({behavior: 'smooth'});
        }
        </script>
    </body>
    </html>
    '''
    
    return HttpResponse(html_content)

@csrf_exempt
def upload_lameness_video(request):
    """Загрузка видео"""
    print("DEBUG: Начало загрузки видео")
    
    try:
        video_file = request.FILES.get('video')
        
        if not video_file:
            return JsonResponse({'success': False, 'error': 'Нет файла'}, status=400)
        
        # Создаем ID
        video_id = str(uuid.uuid4())[:8]
        
        # Сохраняем
        upload_dir = Path("/home/ais/shared/horseAI/media/uploads/lameness")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        video_path = upload_dir / f"{video_id}_{video_file.name}"
        
        print(f"DEBUG: Сохраняю видео: {video_path}")
        
        with open(video_path, 'wb') as f:
            for chunk in video_file.chunks():
                f.write(chunk)
        
        # Статус
        analysis_status[video_id] = {
            'status': 'processing',
            'video_path': str(video_path),
            'video_name': video_file.name,
            'start_time': time.time()
        }
        
        print(f"DEBUG: Статус установлен для {video_id}")
        
        # Запускаем анализ
        import threading
        thread = threading.Thread(target=run_lameness_analysis, args=(video_id, video_path))
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'success': True,
            'video_id': video_id,
            'message': 'Видео загружено'
        })
        
    except Exception as e:
        print(f"DEBUG: Ошибка загрузки: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def run_lameness_analysis(video_id, video_path):
    """Анализ видео"""
    print(f"DEBUG: Начало анализа {video_id}")
    
    try:
        detector_path = Path("/home/ais/shared/horseAI/final_real_detector.py")
        
        if not detector_path.exists():
            analysis_status[video_id] = {'status': 'failed', 'error': 'Детектор не найден'}
            return
        
        cmd = ["python", str(detector_path), video_id, str(video_path)]
        
        print(f"DEBUG: Запускаю команду: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        print(f"DEBUG: Анализ завершен, код: {result.returncode}")
        
        # Парсим результат
        import re
        json_match = re.search(r'🎯 JSON результат для API:\s*(\{.*\})', result.stdout, re.DOTALL)
        
        if json_match:
            result_data = json.loads(json_match.group(1))
            print(f"DEBUG: Получен результат: {list(result_data.keys())}")
            
            analysis_status[video_id] = {
                'status': 'completed',
                'result': result_data,
                'processing_time': round(time.time() - analysis_status[video_id]['start_time'], 2)
            }
        else:
            print(f"DEBUG: Не найден JSON в выводе")
            analysis_status[video_id] = {
                'status': 'failed',
                'error': 'Нет результата в выводе',
                'stdout': result.stdout[-500:],
                'stderr': result.stderr[-200:]
            }
            
    except Exception as e:
        print(f"DEBUG: Ошибка анализа: {e}")
        analysis_status[video_id] = {'status': 'failed', 'error': str(e)}

def get_lameness_status(request, video_id):
    """Получение статуса"""
    print(f"DEBUG: Запрос статуса для {video_id}")
    
    if video_id not in analysis_status:
        print(f"DEBUG: {video_id} не найден")
        return JsonResponse({'status': 'not_found'}, status=404)
    
    status_data = analysis_status[video_id].copy()
    
    if status_data['status'] == 'processing':
        elapsed = time.time() - status_data['start_time']
        status_data['elapsed_seconds'] = round(elapsed, 2)
    
    print(f"DEBUG: Возвращаю статус: {status_data.get('status')}")
    return JsonResponse(status_data)

def download_annotated_video(request, video_id):
    """Скачивание видео"""
    try:
        # Пытаемся найти видео
        output_dir = Path("/home/ais/shared/horseAI/data/output")
        
        # Ищем файл
        pattern = f"*{video_id}*labeled*.mp4"
        matches = list(output_dir.glob(pattern))
        
        if not matches:
            # Пробуем другой паттерн
            pattern = f"{video_id}_*.mp4"
            matches = list(output_dir.glob(pattern))
        
        if not matches:
            return JsonResponse({'error': 'Видео не найдено'}, status=404)
        
        video_path = matches[0]
        
        response = FileResponse(open(video_path, 'rb'))
        response['Content-Type'] = 'video/mp4'
        response['Content-Disposition'] = f'attachment; filename="annotated_{video_id}.mp4"'
        
        print(f"DEBUG: Отдаю видео: {video_path}")
        return response
        
    except Exception as e:
        print(f"DEBUG: Ошибка скачивания: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def test_page(request):
    """Тестовая страница"""
    html = f'''
    <h1>Тестовая страница</h1>
    <p>Всего анализов: {len(analysis_status)}</p>
    <ul>
    '''
    
    for vid, data in analysis_status.items():
        html += f'<li>{vid}: {data.get("status")} - {data.get("video_name", "")}</li>'
    
    html += '</ul><a href="/upload-lameness/">← Назад</a>'
    
    return HttpResponse(html)
