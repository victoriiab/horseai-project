<script>
// Глобальные переменные
let analysisData = null;
let analysisId = null;

// Вспомогательные функции
function getCSRFToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfInput ? csrfInput.value : '';
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.cssText = `
        position: fixed;
        top: 30px;
        right: 30px;
        padding: 16px 24px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: 600;
        z-index: 9999;
        animation: slideIn 0.3s ease;
        max-width: 350px;
        background: ${type === 'success' ? 'var(--success)' : 'var(--error)'};
        color: white;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    `;
    
    const icon = type === 'success' ? '✅' : '❌';
    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    
    const oldToast = document.querySelector('.toast');
    if (oldToast) oldToast.remove();
    
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Загрузка данных анализа
async function loadAnalysisData() {
    try {
        // Получаем ID из URL
        const path = window.location.pathname;
        const match = path.match(/\/analysis\/(\d+)\//);
        if (!match) {
            throw new Error('ID анализа не найден в URL');
        }
        
        analysisId = match[1];
        console.log(`Загружаем анализ ID: ${analysisId}`);
        
        // Загружаем данные анализа
        const response = await fetch(`/api/analysis/${analysisId}/detail/`);
        if (!response.ok) {
            throw new Error(`HTTP ошибка: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Данные анализа:', data);
        
        if (data.success && data.analysis) {
            analysisData = data.analysis;
            renderAnalysis();
            loadReports();
        } else {
            throw new Error(data.error || 'Ошибка загрузки данных');
        }
        
    } catch (error) {
        console.error('Ошибка загрузки анализа:', error);
        showToast('Ошибка загрузки данных анализа', 'error');
        
        // Показываем сообщение об ошибке
        document.querySelector('.analysis-detail-container').innerHTML = `
            <div style="text-align: center; padding: 100px 20px;">
                <div style="font-size: 48px; margin-bottom: 20px;">❌</div>
                <h2 style="color: var(--text-primary); margin-bottom: 15px;">Ошибка загрузки анализа</h2>
                <p style="color: var(--text-secondary); margin-bottom: 30px;">${error.message}</p>
                <button onclick="window.history.back()" style="padding: 12px 24px; background: var(--accent); color: white; border: none; border-radius: 8px; cursor: pointer;">
                    Вернуться назад
                </button>
            </div>
        `;
    }
}

// Отображение данных анализа
function renderAnalysis() {
    if (!analysisData) return;
    
    console.log('Render analysis data:', analysisData);
    
    // Шапка анализа
    const metaHTML = `
        <div class="meta-item">
            <span class="meta-label">Лошадь</span>
            <span class="meta-value">
                <span>🐴</span>
                ${analysisData.animal_name || 'Неизвестно'}
            </span>
        </div>
        <div class="meta-item">
            <span class="meta-label">Дата анализа</span>
            <span class="meta-value">
                <span>📅</span>
                ${new Date(analysisData.created_at || Date.now()).toLocaleDateString('ru-RU')}
            </span>
        </div>
        <div class="meta-item">
            <span class="meta-label">Видео</span>
            <span class="meta-value">
                <span>🎥</span>
                ${analysisData.video_filename || 'Без названия'}
            </span>
        </div>
    `;
    
    document.getElementById('analysisMeta').innerHTML = metaHTML;
    
    // Статус
    const statusElement = document.getElementById('analysisStatus');
    const isLame = analysisData.is_lame || false;
    if (isLame) {
        statusElement.className = 'analysis-status status-lame';
        statusElement.innerHTML = '<span>⚠️</span> Обнаружена хромота';
    } else {
        statusElement.className = 'analysis-status status-healthy';
        statusElement.innerHTML = '<span>✅</span> Здоровая походка';
    }
    
    // Метрики
    const probability = analysisData.lameness_probability || 0;
    const confidence = analysisData.lameness_confidence || analysisData.confidence_score || 0;
    
    document.getElementById('lamenessProbability').textContent = `${probability.toFixed(1)}%`;
    document.getElementById('probabilityBar').style.width = `${Math.min(probability, 100)}%`;
    
    let probabilityDescription = 'Низкая вероятность хромоты';
    if (probability > 70) probabilityDescription = 'Высокая вероятность хромоты';
    else if (probability > 30) probabilityDescription = 'Средняя вероятность хромоты';
    document.getElementById('probabilityDescription').textContent = probabilityDescription;
    
    document.getElementById('analysisConfidence').textContent = `${confidence.toFixed(1)}%`;
    
    const confidenceDot = document.getElementById('confidenceDot');
    if (confidence > 70) {
        confidenceDot.className = 'confidence-dot confidence-high';
    } else if (confidence > 40) {
        confidenceDot.className = 'confidence-dot confidence-medium';
    } else {
        confidenceDot.className = 'confidence-dot confidence-low';
    }
    
    let confidenceDescription = 'Высокая уверенность';
    if (confidence < 40) confidenceDescription = 'Низкая уверенность';
    else if (confidence < 70) confidenceDescription = 'Средняя уверенность';
    document.getElementById('confidenceDescription').textContent = confidenceDescription;
    
    // Видео
    const originalVideo = document.getElementById('originalVideoPlayer');
    const annotatedVideo = document.getElementById('annotatedVideoPlayer');
    
    if (analysisData.video_path) {
        originalVideo.innerHTML = `
            <video controls style="width: 100%; height: 100%; object-fit: contain;">
                <source src="${analysisData.video_path}" type="video/mp4">
                Ваш браузер не поддерживает видео.
            </video>
        `;
    } else {
        originalVideo.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--text-secondary);">
                <div style="font-size: 48px; margin-bottom: 16px;">🎥</div>
                <div>Оригинальное видео не найдено</div>
            </div>
        `;
    }
    
    if (analysisData.annotated_video_path) {
        annotatedVideo.innerHTML = `
            <video controls style="width: 100%; height: 100%; object-fit: contain;">
                <source src="${analysisData.annotated_video_path}" type="video/mp4">
                Ваш браузер не поддерживает видео.
            </video>
        `;
    } else {
        annotatedVideo.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--text-secondary);">
                <div style="font-size: 48px; margin-bottom: 16px;">🎯</div>
                <div>Размеченное видео не найдено</div>
                <small style="margin-top: 10px; color: var(--text-tertiary);">
                    ML модель не сгенерировала видео с разметкой
                </small>
            </div>
        `;
    }
    
    // Обновляем информацию о видео
    if (analysisData.video_path) {
        document.getElementById('originalFormat').textContent = 'MP4';
        // Для размера можно сделать дополнительный запрос, но пока оставим так
    }
}

// Загрузка отчетов
async function loadReports() {
    if (!analysisData) return;
    
    console.log('Loading reports for:', analysisData);
    
    try {
        // Текстовый отчет
        if (analysisData.text_report_path) {
            try {
                const response = await fetch(analysisData.text_report_path);
                if (response.ok) {
                    const text = await response.text();
                    document.getElementById('textReport').textContent = text;
                } else {
                    document.getElementById('textReport').textContent = 'Текстовый отчет не найден по указанному пути';
                }
            } catch (e) {
                document.getElementById('textReport').textContent = 'Ошибка загрузки текстового отчета: ' + e.message;
            }
        } else {
            document.getElementById('textReport').textContent = 'Текстовый отчет не доступен';
        }
        
        // Графический отчет
        if (analysisData.graphic_report_path) {
            document.getElementById('graphicReportImage').src = analysisData.graphic_report_path;
            document.getElementById('graphicReportImage').onerror = function() {
                this.style.display = 'none';
                document.getElementById('graphicReport').innerHTML = `
                    <div style="text-align: center; padding: 50px 20px; color: var(--text-secondary);">
                        <div style="font-size: 48px; margin-bottom: 16px;">📊</div>
                        <div>Графический отчет не найден</div>
                    </div>
                `;
            };
        } else {
            document.getElementById('graphicReport').innerHTML = `
                <div style="text-align: center; padding: 50px 20px; color: var(--text-secondary);">
                    <div style="font-size: 48px; margin-bottom: 16px;">📊</div>
                    <div>Графический отчет не доступен</div>
                </div>
            `;
        }
        
        // Данные поз
        if (analysisData.pose_data_path) {
            document.getElementById('dataReport').textContent = 
                `Файл данных поз: ${analysisData.pose_data_path}\n\n` +
                `Модель: SuperAnimal Quadruped HRNet W32\n` +
                `Формат: HDF5 (H5)\n` +
                `Содержит координаты ключевых точек тела лошади`;
        } else {
            document.getElementById('dataReport').textContent = 'Данные поз (H5 файл) не доступны';
        }
        
    } catch (error) {
        console.error('Ошибка загрузки отчетов:', error);
        document.getElementById('textReport').textContent = 'Ошибка загрузки отчетов: ' + error.message;
    }
}

// Переключение между отчетами
function switchReport(type, event) {
    if (event) {
        // Обновляем активные табы
        document.querySelectorAll('.report-tab').forEach(tab => tab.classList.remove('active'));
        event.target.classList.add('active');
    }
    
    // Показываем выбранный контент
    document.getElementById('textReport').style.display = type === 'text' ? 'block' : 'none';
    document.getElementById('graphicReport').style.display = type === 'graphic' ? 'block' : 'none';
    document.getElementById('dataReport').style.display = type === 'data' ? 'block' : 'none';
}

// Скачивание файлов
function downloadFile(type) {
    if (!analysisData) {
        showToast('Данные анализа не загружены', 'error');
        return;
    }
    
    let url;
    let filename;
    
    if (type === 'original') {
        url = analysisData.video_path;
        filename = analysisData.video_filename || 'original_video.mp4';
    } else if (type === 'annotated') {
        url = analysisData.annotated_video_path;
        filename = (analysisData.video_filename || 'video') + '_annotated.mp4';
    }
    
    if (url) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showToast('Начинается скачивание файла', 'success');
    } else {
        showToast('Файл не найден', 'error');
    }
}

function downloadReport(type) {
    if (!analysisData) {
        showToast('Данные анализа не загружены', 'error');
        return;
    }
    
    let url;
    let filename;
    
    if (type === 'text') {
        url = analysisData.text_report_path;
        filename = (analysisData.video_filename || 'analysis') + '_report.txt';
    } else if (type === 'graphic') {
        url = analysisData.graphic_report_path;
        filename = (analysisData.video_filename || 'analysis') + '_graphic.png';
    } else if (type === 'data') {
        url = analysisData.pose_data_path;
        filename = (analysisData.video_filename || 'analysis') + '_pose_data.h5';
    }
    
    if (url) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showToast('Начинается скачивание отчета', 'success');
    } else {
        showToast('Отчет не найден', 'error');
    }
}

// Удаление анализа
async function deleteAnalysis() {
    if (!analysisData) {
        showToast('Данные анализа не загружены', 'error');
        return;
    }
    
    if (!confirm('Вы уверены, что хотите удалить этот анализ?\nЭто действие нельзя отменить.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/analysis/${analysisId}/delete/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Анализ удален', 'success');
            setTimeout(() => {
                window.location.href = '/analysis/results/';
            }, 1500);
        } else {
            showToast(data.error || 'Ошибка удаления', 'error');
        }
    } catch (error) {
        console.error('Ошибка удаления:', error);
        showToast('Ошибка сети при удалении', 'error');
    }
}

// Дополнительные функции
function shareAnalysis() {
    if (!analysisData) {
        showToast('Данные анализа не загружены', 'error');
        return;
    }
    
    const shareData = {
        title: `Анализ походки: ${analysisData.animal_name || 'Лошадь'}`,
        text: `Вероятность хромоты: ${analysisData.lameness_probability || 0}%`,
        url: window.location.href
    };
    
    if (navigator.share) {
        navigator.share(shareData)
            .then(() => showToast('Результат успешно расшарен', 'success'))
            .catch(err => {
                console.error('Ошибка sharing:', err);
                copyToClipboard(window.location.href);
            });
    } else {
        copyToClipboard(window.location.href);
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
        .then(() => showToast('Ссылка скопирована в буфер обмена', 'success'))
        .catch(err => {
            console.error('Ошибка копирования:', err);
            showToast('Не удалось скопировать ссылку', 'error');
        });
}

function printReport() {
    window.print();
}

// Инициализация табов
function initTabs() {
    document.querySelectorAll('.report-tab').forEach((tab, index) => {
        tab.addEventListener('click', function(e) {
            const tabs = ['text', 'graphic', 'data'];
            switchReport(tabs[index], e);
        });
    });
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    console.log('Analysis detail page loaded');
    initTabs();
    loadAnalysisData();
    
    // Назначаем обработчики для кнопок скачивания
    document.querySelectorAll('[onclick^="download"]').forEach(btn => {
        const oldHandler = btn.getAttribute('onclick');
        btn.removeAttribute('onclick');
        btn.addEventListener('click', function() {
            const match = oldHandler.match(/download(\w+)\(['"](.*?)['"]\)/);
            if (match) {
                const func = match[1];
                const arg = match[2];
                if (func === 'File') downloadFile(arg);
                else if (func === 'Report') downloadReport(arg);
            }
        });
    });
    
    // Назначаем обработчики для остальных кнопок
    const actions = {
        'shareAnalysis': shareAnalysis,
        'printReport': printReport,
        'deleteAnalysis': deleteAnalysis
    };
    
    for (const [attr, handler] of Object.entries(actions)) {
        const elements = document.querySelectorAll(`[onclick="${attr}()"]`);
        elements.forEach(el => {
            el.removeAttribute('onclick');
            el.addEventListener('click', handler);
        });
    }
});
</script>

<style>
/* Стили для toast уведомлений */
.toast {
    position: fixed;
    top: 30px;
    right: 30px;
    padding: 16px 24px;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 600;
    z-index: 9999;
    animation: slideIn 0.3s ease;
    max-width: 350px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.toast-success {
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
}

.toast-error {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: white;
}

@keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}
</style>
