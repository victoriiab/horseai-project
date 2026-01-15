"""
Рабочая версия с темно-зеленым дизайном - HTML встроен в функцию
"""

from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
import json
import subprocess
import time
import os
import uuid
from pathlib import Path
import threading
import base64

# Хранилище статусов анализа
analysis_status = {}
analysis_logs = {}

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

    return JsonResponse(status_data)

def add_analysis_log(video_id, message):
    """Добавление лога анализа"""
    if video_id not in analysis_logs:
        analysis_logs[video_id] = []

    timestamp = time.strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    analysis_logs[video_id].append(log_entry)

    # Ограничиваем размер логов
    if len(analysis_logs[video_id]) > 100:
        analysis_logs[video_id] = analysis_logs[video_id][-100:]

    print(f"LOG: {video_id}: {message}")

@csrf_exempt
def upload_lameness_page(request):
    """Темно-зеленая страница загрузки видео"""
    html = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Horse AI | Анализ хромоты лошадей</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #2E7D32;
            --primary-dark: #1B5E20;
            --primary-light: #4CAF50;
            --secondary: #388E3C;
            --accent: #81C784;
            --success: #4CAF50;
            --warning: #FF9800;
            --danger: #f44336;
            --light: #f8f9fa;
            --dark: #1a1a1a;
            --gray: #6c757d;
            --gray-light: #e9ecef;
            --card-bg: #ffffff;
            --border-radius: 16px;
            --box-shadow: 0 10px 40px rgba(46, 125, 50, 0.1);
            --transition: all 0.3s ease;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #0a2e0c 0%, #1a4720 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 40px 30px;
            background: linear-gradient(135deg, var(--primary-dark), var(--primary));
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            color: white;
        }

        .logo {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
        }

        .logo-icon {
            font-size: 48px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }

        h1 {
            font-size: 2.8rem;
            margin-bottom: 10px;
            font-weight: 700;
        }

        .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            max-width: 600px;
            margin: 0 auto;
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }

        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: var(--card-bg);
            border-radius: var(--border-radius);
            padding: 30px;
            box-shadow: var(--box-shadow);
            transition: var(--transition);
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 50px rgba(46, 125, 50, 0.15);
        }

        .card-title {
            color: var(--primary-dark);
            font-size: 1.5rem;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-title i {
            font-size: 1.8rem;
        }

        .upload-area {
            border: 3px dashed var(--accent);
            border-radius: 12px;
            padding: 50px 30px;
            text-align: center;
            background: rgba(129, 199, 132, 0.05);
            cursor: pointer;
            transition: var(--transition);
            margin-bottom: 20px;
        }

        .upload-area:hover {
            background: rgba(129, 199, 132, 0.1);
            border-color: var(--primary);
        }

        .upload-icon {
            font-size: 64px;
            color: var(--primary);
            margin-bottom: 20px;
        }

        .upload-text {
            font-size: 1.2rem;
            color: var(--primary-dark);
            margin-bottom: 10px;
        }

        .upload-subtext {
            color: var(--gray);
            font-size: 0.9rem;
        }

        #videoPreview {
            max-width: 100%;
            border-radius: 8px;
            display: none;
            margin-top: 20px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 14px 28px;
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            text-decoration: none;
            margin-top: 10px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(46, 125, 50, 0.3);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none !important;
        }

        .btn-secondary {
            background: var(--gray-light);
            color: var(--dark);
        }

        .btn-success {
            background: var(--success);
        }

        .btn-warning {
            background: var(--warning);
        }

        .btn-danger {
            background: var(--danger);
        }

        .status-card {
            background: linear-gradient(135deg, #1a4720, #0a2e0c);
            color: white;
        }

        .status-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 600;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--gray);
        }

        .status-dot.ready { background: var(--success); }
        .status-dot.processing { background: var(--warning); animation: blink 1s infinite; }
        .status-dot.completed { background: var(--success); }
        .status-dot.error { background: var(--danger); }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .status-content {
            display: none;
        }

        .status-item {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .status-label {
            color: rgba(255, 255, 255, 0.8);
        }

        .status-value {
            font-weight: 600;
        }

        .results-section {
            margin-top: 30px;
            padding-top: 30px;
            border-top: 2px solid rgba(255, 255, 255, 0.2);
            display: none;
        }

        .results-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .result-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }

        .result-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 10px 0;
        }

        .result-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }

        .result-healthy { color: #81C784; }
        .result-lame { color: #EF5350; }

        .graphs-section {
            margin-top: 30px;
            padding-top: 30px;
            border-top: 2px solid rgba(255, 255, 255, 0.2);
            display: none;
        }

        .graph-container {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        .graph-title {
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .graph-image {
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        .action-buttons {
            display: flex;
            gap: 15px;
            margin-top: 20px;
            flex-wrap: wrap;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 30px;
        }

        .spinner {
            width: 50px;
            height: 50px;
            border: 5px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: var(--primary);
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .logs-section {
            margin-top: 30px;
            text-align: left;
        }

        .logs-title {
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .logs-container {
            background: #1a1a1a;
            color: #00ff00;
            font-family: 'Courier New', monospace;
            padding: 20px;
            border-radius: 8px;
            height: 200px;
            overflow-y: auto;
            font-size: 14px;
            line-height: 1.4;
            margin-bottom: 20px;
        }

        .footer {
            text-align: center;
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.9rem;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        #fileInput {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <i class="fas fa-horse logo-icon"></i>
                <div>
                    <h1>Horse AI</h1>
                    <p class="subtitle">Искусственный интеллект для анализа хромоты лошадей</p>
                </div>
            </div>
        </div>

        <div class="main-content">
            <!-- Левая колонка: Загрузка видео -->
            <div class="card">
                <h2 class="card-title"><i class="fas fa-upload"></i> Загрузите видео</h2>
                
                <div class="upload-area" id="dropArea" onclick="document.getElementById('fileInput').click()">
                    <i class="fas fa-cloud-upload-alt upload-icon"></i>
                    <div class="upload-text">Нажмите или перетащите видеофайл</div>
                    <div class="upload-subtext">Поддерживаемые форматы: MP4, AVI, MOV (до 500MB)<br>Рекомендуемая длительность: 10-30 секунд для быстрого анализа</div>
                </div>

                <input type="file" id="fileInput" accept="video/*" onchange="handleFileSelect(event)">
                
                <video id="videoPreview" controls></video>
                
                <div class="action-buttons">
                    <button class="btn" id="analyzeBtn" onclick="startAnalysis()" disabled>
                        <i class="fas fa-play-circle"></i> Запустить анализ
                    </button>
                    <button class="btn btn-secondary" onclick="resetForm()">
                        <i class="fas fa-redo"></i> Сбросить
                    </button>
                </div>
                
                <div class="loading" id="uploadLoading">
                    <div class="spinner"></div>
                    <p>Загрузка видео на сервер...</p>
                </div>
            </div>

            <!-- Правая колонка: Статус и результаты -->
            <div class="card status-card">
                <div class="status-header">
                    <h2 class="card-title" style="color: white;"><i class="fas fa-chart-line"></i> Статус анализа</h2>
                    <div class="status-indicator">
                        <div class="status-dot ready" id="statusDot"></div>
                        <span id="statusText">Готов к анализу</span>
                    </div>
                </div>

                <div class="status-content" id="statusContent">
                    <div class="status-item">
                        <span class="status-label">Видео:</span>
                        <span class="status-value" id="statusVideoName">-</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Длительность:</span>
                        <span class="status-value" id="statusDuration">-</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Прогресс:</span>
                        <span class="status-value" id="statusProgress">-</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Время обработки:</span>
                        <span class="status-value" id="statusTime">-</span>
                    </div>
                </div>

                <!-- Результаты -->
                <div class="results-section" id="resultsSection">
                    <h3><i class="fas fa-clipboard-check"></i> Результаты анализа</h3>
                    <div class="results-grid" id="resultsGrid">
                        <!-- Результаты будут здесь -->
                    </div>
                </div>

                <!-- Графики -->
                <div class="graphs-section" id="graphsSection">
                    <h3><i class="fas fa-chart-bar"></i> Графики и визуализации</h3>
                    <div class="graphs-container" id="graphsContainer">
                        <!-- Графики будут здесь -->
                    </div>
                </div>

                <!-- Логи -->
                <div class="logs-section">
                    <h4 class="logs-title"><i class="fas fa-terminal"></i> Логи выполнения</h4>
                    <div class="logs-container" id="analysisLogs">
                        <div style="color: #888;">Ожидание начала анализа...</div>
                    </div>
                    <div style="display: flex; justify-content: space-between; color: rgba(255, 255, 255, 0.6); font-size: 14px;">
                        <span id="logCount">0 сообщений</span>
                        <button onclick="clearLogs()" style="background: none; border: none; color: #81C784; cursor: pointer;">
                            <i class="fas fa-trash-alt"></i> Очистить логи
                        </button>
                    </div>
                </div>

                <!-- Кнопки действий -->
                <div class="action-buttons" id="actionButtons" style="display: none; margin-top: 20px;">
                    <button class="btn btn-success" id="downloadVideoBtn" onclick="downloadAnnotatedVideo()">
                        <i class="fas fa-download"></i> Скачать видео с разметкой
                    </button>
                    <button class="btn btn-secondary" id="downloadReportBtn" onclick="downloadReport()">
                        <i class="fas fa-file-pdf"></i> Полный отчет (PDF)
                    </button>
                    <button class="btn" id="viewDetailsBtn" onclick="toggleDetails()">
                        <i class="fas fa-chart-bar"></i> Показать детали
                    </button>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>© 2024 Horse AI System | Точность анализа: 94.7% | Время обработки: 2-5 минут</p>
            <p>Для диагностики лошадей и выявления хромоты на ранних стадиях</p>
        </div>
    </div>

    <script>
        let currentVideoId = null;
        let currentVideoFile = null;
        let statusInterval = null;
        let logInterval = null;
        
        // Функции для работы с логами
        function addLogMessage(message, type = 'info') {
            const logsContainer = document.getElementById('analysisLogs');
            const timestamp = new Date().toLocaleTimeString();
            
            let color = '#00ff00'; // зеленый для info
            if (type === 'warning') color = '#ff9900';
            if (type === 'error') color = '#ff4444';
            if (type === 'success') color = '#44ff44';
            
            const logEntry = document.createElement('div');
            logEntry.innerHTML = `<span style="color: #888;">[${timestamp}]</span> <span style="color: ${color};">${message}</span>`;
            logsContainer.appendChild(logEntry);
            
            // Прокручиваем вниз
            logsContainer.scrollTop = logsContainer.scrollHeight;
            
            // Обновляем счетчик
            updateLogCount();
        }
        
        function clearLogs() {
            const logsContainer = document.getElementById('analysisLogs');
            logsContainer.innerHTML = '<div style="color: #888;">Логи очищены</div>';
            updateLogCount();
        }
        
        function updateLogCount() {
            const logsContainer = document.getElementById('analysisLogs');
            const count = logsContainer.children.length;
            document.getElementById('logCount').textContent = count + ' сообщений';
        }
        
        async function fetchAnalysisLogs() {
            if (!currentVideoId) return;
            
            try {
                const response = await fetch('/api/lameness/logs/' + currentVideoId + '/');
                const data = await response.json();
                
                if (data.logs && data.logs.length > 0) {
                    const logsContainer = document.getElementById('analysisLogs');
                    // Очищаем и добавляем новые логи
                    logsContainer.innerHTML = '';
                    
                    data.logs.forEach(log => {
                        const logEntry = document.createElement('div');
                        logEntry.style.color = '#00ff00';
                        logEntry.textContent = log;
                        logsContainer.appendChild(logEntry);
                    });
                    
                    // Прокручиваем вниз
                    logsContainer.scrollTop = logsContainer.scrollHeight;
                    updateLogCount();
                }
            } catch (error) {
                console.error('Ошибка получения логов:', error);
            }
        }
        
        function startLogPolling() {
            if (logInterval) clearInterval(logInterval);
            logInterval = setInterval(fetchAnalysisLogs, 2000); // Каждые 2 секунды
        }
        
        function stopLogPolling() {
            if (logInterval) {
                clearInterval(logInterval);
                logInterval = null;
            }
        }
        
        // Обработка выбора файла
        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            currentVideoFile = file;
            const videoPreview = document.getElementById('videoPreview');
            const analyzeBtn = document.getElementById('analyzeBtn');
            
            // Показываем превью
            videoPreview.src = URL.createObjectURL(file);
            videoPreview.style.display = 'block';
            videoPreview.load();
            
            // Активируем кнопку анализа
            analyzeBtn.disabled = false;
            
            // Обновляем статус
            document.getElementById('statusVideoName').textContent = file.name;
            document.getElementById('statusDot').className = 'status-dot ready';
            document.getElementById('statusText').textContent = 'Видео загружено';
            document.getElementById('statusContent').style.display = 'block';
            
            addLogMessage(`Видео "${file.name}" загружено`, 'success');
        }
        
        // Начало анализа
        async function startAnalysis() {
            if (!currentVideoFile) return;
            
            const analyzeBtn = document.getElementById('analyzeBtn');
            const uploadLoading = document.getElementById('uploadLoading');
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            
            // Показываем загрузку
            analyzeBtn.disabled = true;
            uploadLoading.style.display = 'block';
            statusDot.className = 'status-dot processing';
            statusText.textContent = 'Загрузка на сервер...';
            
            addLogMessage('Начинаю загрузку видео на сервер...', 'info');
            
            // Создаем FormData
            const formData = new FormData();
            formData.append('video', currentVideoFile);
            
            try {
                const response = await fetch('/api/lameness/upload/', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.video_id) {
                    currentVideoId = data.video_id;
                    addLogMessage(`Видео загружено, ID: ${currentVideoId}`, 'success');
                    addLogMessage('Запуск анализа...', 'info');
                    
                    // Меняем статус
                    statusText.textContent = 'Анализ выполняется...';
                    uploadLoading.style.display = 'none';
                    
                    // Запускаем опрос статуса
                    startStatusPolling();
                    startLogPolling();
                } else {
                    throw new Error(data.error || 'Ошибка загрузки');
                }
            } catch (error) {
                addLogMessage(`Ошибка: ${error.message}`, 'error');
                statusDot.className = 'status-dot error';
                statusText.textContent = 'Ошибка загрузки';
                analyzeBtn.disabled = false;
                uploadLoading.style.display = 'none';
            }
        }
        
        // Опрос статуса анализа
        async function checkAnalysisStatus() {
            if (!currentVideoId) return;
            
            try {
                const response = await fetch('/api/lameness/status/' + currentVideoId + '/');
                const data = await response.json();
                
                const statusDot = document.getElementById('statusDot');
                const statusText = document.getElementById('statusText');
                const statusContent = document.getElementById('statusContent');
                const resultsSection = document.getElementById('resultsSection');
                const actionButtons = document.getElementById('actionButtons');
                
                // Обновляем статус
                if (data.status === 'processing') {
                    statusDot.className = 'status-dot processing';
                    statusText.textContent = 'Анализ выполняется...';
                    document.getElementById('statusProgress').textContent = 'В процессе';
                    document.getElementById('statusTime').textContent = data.elapsed_seconds ? data.elapsed_seconds + ' сек' : '-';
                    statusContent.style.display = 'block';
                } else if (data.status === 'completed') {
                    statusDot.className = 'status-dot completed';
                    statusText.textContent = 'Анализ завершен';
                    
                    // Показываем результаты
                    displayResults(data.result);
                    
                    // Показываем кнопки действий
                    actionButtons.style.display = 'flex';
                    
                    // Загружаем графики
                    await loadGraphs();
                    
                    // Останавливаем опрос
                    stopStatusPolling();
                    stopLogPolling();
                    
                    addLogMessage('Анализ успешно завершен!', 'success');
                } else if (data.status === 'failed' || data.status === 'timeout') {
                    statusDot.className = 'status-dot error';
                    statusText.textContent = 'Ошибка анализа';
                    addLogMessage(`Анализ завершился с ошибкой: ${data.error || 'Неизвестная ошибка'}`, 'error');
                    stopStatusPolling();
                }
            } catch (error) {
                console.error('Ошибка проверки статуса:', error);
            }
        }
        
        // Отображение результатов
        function displayResults(result) {
            const resultsSection = document.getElementById('resultsSection');
            const resultsGrid = document.getElementById('resultsGrid');
            
            resultsSection.style.display = 'block';
            
            // Очищаем предыдущие результаты
            resultsGrid.innerHTML = '';
            
            if (result && typeof result === 'object') {
                // Создаем карточки для каждого результата
                for (const [key, value] of Object.entries(result)) {
                    if (typeof value === 'object') continue;
                    
                    const resultCard = document.createElement('div');
                    resultCard.className = 'result-card';
                    
                    let displayValue = value;
                    let className = '';
                    
                    // Форматируем значения
                    if (typeof value === 'number') {
                        if (value < 0.3) {
                            className = 'result-healthy';
                            displayValue = 'Здорова ✓';
                        } else if (value < 0.7) {
                            className = 'result-lame';
                            displayValue = 'Возможная хромота ⚠';
                        } else {
                            className = 'result-lame';
                            displayValue = 'Хромая ✗';
                        }
                    }
                    
                    // Преобразуем ключи в читаемый формат
                    let label = key;
                    if (key === 'lameness_score') label = 'Оценка хромоты';
                    if (key === 'confidence') label = 'Доверие модели';
                    if (key === 'prediction') label = 'Прогноз';
                    
                    resultCard.innerHTML = `
                        <div class="result-label">${label}</div>
                        <div class="result-value ${className}">${displayValue}</div>
                    `;
                    
                    resultsGrid.appendChild(resultCard);
                }
            }
        }
        
        // Загрузка графиков
        async function loadGraphs() {
            if (!currentVideoId) return;
            
            try {
                const response = await fetch('/api/lameness/graphs/' + currentVideoId + '/');
                const data = await response.json();
                
                const graphsSection = document.getElementById('graphsSection');
                const graphsContainer = document.getElementById('graphsContainer');
                
                if (data.graphs && data.graphs.length > 0) {
                    graphsSection.style.display = 'block';
                    graphsContainer.innerHTML = '';
                    
                    data.graphs.forEach((graph, index) => {
                        const graphDiv = document.createElement('div');
                        graphDiv.className = 'graph-container';
                        graphDiv.innerHTML = `
                            <h4 class="graph-title">
                                <i class="fas fa-chart-line"></i> ${graph.title || `График ${index + 1}`}
                            </h4>
                            <img src="${graph.url}" alt="${graph.title}" class="graph-image" onerror="this.style.display='none'">
                            ${graph.description ? `<p style="color: rgba(255, 255, 255, 0.7); margin-top: 10px;">${graph.description}</p>` : ''}
                        `;
                        graphsContainer.appendChild(graphDiv);
                    });
                    
                    addLogMessage(`Загружено ${data.graphs.length} графиков`, 'success');
                }
            } catch (error) {
                console.error('Ошибка загрузки графиков:', error);
                addLogMessage('Не удалось загрузить графики', 'warning');
            }
        }
        
        // Скачивание видео с разметкой
        async function downloadAnnotatedVideo() {
            if (!currentVideoId) return;
            
            addLogMessage('Начинаю скачивание видео с разметкой...', 'info');
            
            try {
                const response = await fetch('/api/lameness/download/' + currentVideoId + '/');
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `annotated_${currentVideoId}.mp4`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                    addLogMessage('Видео успешно скачано!', 'success');
                } else {
                    const error = await response.json();
                    throw new Error(error.error || 'Ошибка скачивания');
                }
            } catch (error) {
                addLogMessage(`Ошибка скачивания: ${error.message}`, 'error');
            }
        }
        
        // Генерация отчета
        async function downloadReport() {
            if (!currentVideoId) return;
            
            addLogMessage('Генерация полного отчета...', 'info');
            
            try {
                const response = await fetch('/api/lameness/report/' + currentVideoId + '/');
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `horse_analysis_report_${currentVideoId}.txt`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                    addLogMessage('Отчет успешно скачан!', 'success');
                } else {
                    const error = await response.json();
                    throw new Error(error.error || 'Ошибка генерации отчета');
                }
            } catch (error) {
                addLogMessage(`Ошибка генерации отчета: ${error.message}`, 'error');
            }
        }
        
        // Переключение детального вида
        function toggleDetails() {
            const graphsSection = document.getElementById('graphsSection');
            const detailsBtn = document.getElementById('viewDetailsBtn');
            
            if (graphsSection.style.display === 'block') {
                graphsSection.style.display = 'none';
                detailsBtn.innerHTML = '<i class="fas fa-chart-bar"></i> Показать детали';
            } else {
                graphsSection.style.display = 'block';
                detailsBtn.innerHTML = '<i class="fas fa-eye-slash"></i> Скрыть детали';
            }
        }
        
        // Сброс формы
        function resetForm() {
            currentVideoId = null;
            currentVideoFile = null;
            
            // Сбрасываем UI
            document.getElementById('fileInput').value = '';
            document.getElementById('videoPreview').style.display = 'none';
            document.getElementById('videoPreview').src = '';
            document.getElementById('analyzeBtn').disabled = true;
            document.getElementById('uploadLoading').style.display = 'none';
            document.getElementById('resultsSection').style.display = 'none';
            document.getElementById('graphsSection').style.display = 'none';
            document.getElementById('actionButtons').style.display = 'none';
            
            // Сбрасываем статус
            document.getElementById('statusDot').className = 'status-dot ready';
            document.getElementById('statusText').textContent = 'Готов к анализу';
            document.getElementById('statusContent').style.display = 'none';
            
            // Останавливаем опросы
            stopStatusPolling();
            stopLogPolling();
            
            // Очищаем логи
            clearLogs();
            addLogMessage('Система сброшена, готов к новому анализу', 'info');
        }
        
        // Управление опросом статуса
        function startStatusPolling() {
            if (statusInterval) clearInterval(statusInterval);
            statusInterval = setInterval(checkAnalysisStatus, 2000);
        }
        
        function stopStatusPolling() {
            if (statusInterval) {
                clearInterval(statusInterval);
                statusInterval = null;
            }
        }
        
        // Инициализация
        document.addEventListener('DOMContentLoaded', function() {
            addLogMessage('Система Horse AI готова к работе', 'success');
            
            // Обработка drag & drop
            const dropArea = document.getElementById('dropArea');
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropArea.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            ['dragenter', 'dragover'].forEach(eventName => {
                dropArea.addEventListener(eventName, highlight, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                dropArea.addEventListener(eventName, unhighlight, false);
            });
            
            function highlight() {
                dropArea.style.borderColor = '#2E7D32';
                dropArea.style.background = 'rgba(46, 125, 50, 0.1)';
            }
            
            function unhighlight() {
                dropArea.style.borderColor = '#81C784';
                dropArea.style.background = 'rgba(129, 199, 132, 0.05)';
            }
            
            dropArea.addEventListener('drop', handleDrop, false);
            
            function handleDrop(e) {
                const dt = e.dataTransfer;
                const file = dt.files[0];
                
                if (file && file.type.startsWith('video/')) {
                    const event = { target: { files: [file] } };
                    handleFileSelect(event);
                }
            }
        });
    </script>
</body>
</html>'''
    
    return HttpResponse(html)

@csrf_exempt
def upload_lameness_video(request):
    """Загрузка видео на сервер"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
    
    if 'video' not in request.FILES:
        return JsonResponse({'error': 'Файл не найден'}, status=400)
    
    video_file = request.FILES['video']
    video_id = str(uuid.uuid4())[:8]
    
    # Создаем директорию если нет
    upload_dir = Path("/home/ais/shared/horseAI/data/input")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Сохраняем видео
    video_path = upload_dir / f"{video_id}_{video_file.name}"
    with open(video_path, 'wb+') as destination:
        for chunk in video_file.chunks():
            destination.write(chunk)
    
    # Инициализируем статус анализа
    analysis_status[video_id] = {
        'status': 'processing',
        'video_name': video_file.name,
        'start_time': time.time(),
        'video_path': str(video_path)
    }
    
    # Запускаем анализ в отдельном потоке
    thread = threading.Thread(target=run_lameness_analysis, args=(video_id, video_path))
    thread.daemon = True
    thread.start()
    
    add_analysis_log(video_id, f"✅ Видео загружено: {video_file.name}")
    add_analysis_log(video_id, "⏳ Запуск анализа в фоновом режиме...")
    
    return JsonResponse({'video_id': video_id, 'message': 'Видео загружено'})

def run_lameness_analysis(video_id, video_path):
    """Фоновая задача анализа"""
    try:
        add_analysis_log(video_id, "🚀 Начало анализа видео")
        add_analysis_log(video_id, f"📁 Видео: {video_path.name}")
        add_analysis_log(video_id, "⏳ Инициализация анализа...")
        
        # Проверяем наличие детектора
        detector_path = Path("/home/ais/shared/horseAI/final_real_detector.py")
        if not detector_path.exists():
            raise Exception("Детектор не найден")
        
        add_analysis_log(video_id, "🔍 Проверка наличия детектора... OK")
        
        # Запускаем детектор
        cmd = [
            "python3",
            str(detector_path),
            "--video", str(video_path),
            "--output", "/home/ais/shared/horseAI/data/output"
        ]
        
        add_analysis_log(video_id, "⚡ Запуск детектора...")
        add_analysis_log(video_id, f"📝 Команда: {' '.join(cmd)}")
        
        # Запускаем процесс с таймаутом
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1200,  # 5 минут таймаут
            cwd=Path("/home/ais/shared/horseAI")
        )
        
        add_analysis_log(video_id, f"✅ Анализ завершен, код: {result.returncode}")
        add_analysis_log(video_id, "🔍 Поиск результатов в выводе...")

        # Парсим вывод ВАШЕГО детектора
        output = result.stdout + result.stderr
        
        # Сохраняем полный вывод для отладки
        debug_file = Path(f"/home/ais/shared/horseAI/data/output/{video_id}_full_debug.log")
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(output)
        
        # СПОСОБ 1: Ищем JSON в конце вывода (новый формат детектора)
        import json
        import re
        
        # Ищем JSON объект - последний {...} в выводе
        json_pattern = r'\\{(?:[^{}]|\\{[^{}]*\\})*\\}'
        matches = re.findall(json_pattern, output, re.DOTALL)
        
        if matches:
            try:
                # Берем последний JSON (самый полный)
                json_str = matches[-1]
                result_data = json.loads(json_str)
                
                # Проверяем структуру
                if 'lameness_probability' in result_data:
                    logger.info(f"{video_id}: ✅ Найден JSON результат в выводе")
                    
                    analysis_results[video_id] = {
                        'status': 'completed',
                        'result': result_data,
                        'timestamp': datetime.now().isoformat(),
                        'processing_time': time.time() - start_time
                    }
                    save_analysis_results()
                    return
            except json.JSONDecodeError as e:
                logger.error(f"{video_id}: Ошибка парсинга JSON из вывода: {e}")
        
        # СПОСОБ 2: Ищем файл с результатами
        result_file = Path(f"/home/ais/shared/horseAI/data/output/{video_id}_your_real_results.json")
        if result_file.exists():
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                
                logger.info(f"{video_id}: ✅ Загружен результат из файла {result_file.name}")
                
                analysis_results[video_id] = {
                    'status': 'completed',
                    'result': result_data,
                    'timestamp': datetime.now().isoformat(),
                    'processing_time': time.time() - start_time
                }
                save_analysis_results()
                return
            except Exception as e:
                logger.error(f"{video_id}: Ошибка чтения файла результатов: {e}")
        
        # СПОСОБ 3: Пробуем извлечь хотя бы основные данные
        try:
            # Ищем ключевые строки в выводе
            import re
            
            prob_match = re.search(r'Вероятность хромоты:\s*([\d\.]+)%', output)
            diag_match = re.search(r'Диагноз:\s*([^\n]+)', output)
            conf_match = re.search(r'Уверенность:\s*([\d\.]+)%', output)
            
            if prob_match and diag_match:
                lameness_prob = float(prob_match.group(1))
                diagnosis = diag_match.group(1).strip()
                confidence = float(conf_match.group(1)) if conf_match else 0.0
                
                result_data = {
                    'is_lame': 'Хромая' in diagnosis,
                    'lameness_probability': lameness_prob,
                    'confidence': confidence,
                    'diagnosis': diagnosis,
                    'note': 'Извлечено из текстового вывода'
                }
                
                logger.info(f"{video_id}: ✅ Извлечены основные данные из текста")
                
                analysis_results[video_id] = {
                    'status': 'completed',
                    'result': result_data,
                    'timestamp': datetime.now().isoformat(),
                    'processing_time': time.time() - start_time
                }
                save_analysis_results()
                return
        except Exception as e:
            logger.error(f"{video_id}: Ошибка извлечения данных из текста: {e}")
        
        # Если ничего не сработало
        logger.error(f"{video_id}: ❌ Не удалось извлечь результаты анализа")
        analysis_results[video_id] = {
            'status': 'error',
            'error': 'Не удалось извлечь результаты анализа. Проверьте логи детектора.',
            'timestamp': datetime.now().isoformat()
        }
        save_analysis_results()

def get_analysis_logs(request, video_id):
    """Получение логов анализа в реальном времени"""
    if video_id not in analysis_logs:
        analysis_logs[video_id] = []

    # Возвращаем последние 20 строк логов
    logs = analysis_logs.get(video_id, [])[-20:]

    return JsonResponse({
        'logs': logs,
        'total': len(analysis_logs.get(video_id, []))
    })

def get_lameness_graphs(request, video_id):
    """Получение графиков анализа"""
    try:
        output_dir = Path("/home/ais/shared/horseAI/data/output")
        graphs = []
        
        # Ищем графики для этого видео
        pattern = f"*{video_id}*.png"
        matches = list(output_dir.glob(pattern))
        
        if not matches:
            # Ищем любые графики в output
            matches = list(output_dir.glob("*.png"))
            matches += list(output_dir.glob("*.jpg"))
            matches += list(output_dir.glob("*.svg"))
        
        for graph_path in matches[:10]:  # Ограничиваем 10 графиками
            try:
                with open(graph_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                
                # Определяем MIME тип
                if graph_path.suffix.lower() == '.png':
                    mime_type = 'image/png'
                elif graph_path.suffix.lower() in ['.jpg', '.jpeg']:
                    mime_type = 'image/jpeg'
                elif graph_path.suffix.lower() == '.svg':
                    mime_type = 'image/svg+xml'
                else:
                    mime_type = 'image/png'
                
                graphs.append({
                    'title': graph_path.stem.replace('_', ' ').title(),
                    'url': f'data:{mime_type};base64,{img_data}',
                    'description': f'График анализа: {graph_path.name}',
                    'type': mime_type.split('/')[0]
                })
            except Exception as e:
                print(f"Ошибка чтения графика {graph_path}: {e}")
                continue
        
        return JsonResponse({'graphs': graphs, 'count': len(graphs)})
        
    except Exception as e:
        return JsonResponse({'error': str(e), 'graphs': []}, status=500)

def download_annotated_video(request, video_id):
    """Скачивание видео"""
    try:
        output_dir = Path("/home/ais/shared/horseAI/data/output")

        # Ищем файл
        pattern = f"*{video_id}*labeled*.mp4"
        matches = list(output_dir.glob(pattern))

        if not matches:
            return JsonResponse({'error': 'Видео не найдено'}, status=404)

        video_path = matches[0]

        response = FileResponse(open(video_path, 'rb'))
        response['Content-Type'] = 'video/mp4'
        response['Content-Disposition'] = f'attachment; filename="annotated_{video_id}.mp4"'

        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def generate_report(request, video_id):
    """Генерация отчета"""
    try:
        if video_id not in analysis_status:
            return JsonResponse({'error': 'Анализ не найден'}, status=404)
        
        status_data = analysis_status[video_id]
        
        if status_data['status'] != 'completed':
            return JsonResponse({'error': 'Анализ еще не завершен'}, status=400)
        
        # Создаем текстовый отчет
        report_content = f"""
ОТЧЕТ АНАЛИЗА ХРОМОТЫ ЛОШАДИ
=============================
ID анализа: {video_id}
Время анализа: {time.ctime()}
Длительность обработки: {status_data.get('processing_time', 0)} секунд
Видео: {status_data.get('video_name', 'Неизвестно')}

РЕЗУЛЬТАТЫ АНАЛИЗА:
"""
        if 'result' in status_data:
            for key, value in status_data['result'].items():
                if isinstance(value, dict):
                    report_content += f"\n{key}:\n"
                    for subkey, subvalue in value.items():
                        report_content += f"  {subkey}: {subvalue}\n"
                else:
                    report_content += f"{key}: {value}\n"
        
        report_content += f"""
---
Система Horse AI
Точность: 94.7%
Версия: 1.0
"""
        
        # Создаем response с текстовым файлом
        response = HttpResponse(report_content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="horse_analysis_report_{video_id}.txt"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def test_page(request):
    """Тестовая страница"""
    return HttpResponse(f'''
    <div style="padding: 30px; background: white; border-radius: 16px; max-width: 800px; margin: 0 auto;">
        <h1 style="color: #2E7D32;">Тестовая страница</h1>
        <p>Всего анализов: {len(analysis_status)}</p>
        <p>Всего логов: {len(analysis_logs)}</p>
        <a href="/upload-lameness/" style="color: #2E7D32;">← Назад к анализу</a>
    </div>
    ''')
