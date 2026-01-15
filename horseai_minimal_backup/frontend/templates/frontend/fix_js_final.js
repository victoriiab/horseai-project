<script>
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎨 Красивый интерфейс загрузки видео загружен');

    // ЭЛЕМЕНТЫ
    const form = document.getElementById('uploadForm');
    const videoFile = document.getElementById('videoFile');
    const uploadZone = document.getElementById('uploadZone');
    const browseButton = document.getElementById('browseButton');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileMeta = document.getElementById('fileMeta');
    const submitBtn = document.getElementById('submitBtn');
    const progressSection = document.getElementById('progressSection');
    const progressFill = document.getElementById('progressFill');
    const progressPercent = document.getElementById('progressPercent');
    const progressText = document.getElementById('progressText');
    const resultSection = document.getElementById('resultSection');
    const resultGrid = document.getElementById('resultGrid');

    // 1. ОБРАБОТКА ВЫБОРА ФАЙЛА
    browseButton.addEventListener('click', () => {
        videoFile.click();
    });

    videoFile.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleFile(this.files[0]);
        }
    });

    // 2. DRAG & DROP (УПРОЩЕННЫЙ)
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.style.background = 'rgba(76, 175, 80, 0.1)';
        uploadZone.style.borderColor = '#2E7D32';
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.style.background = '';
        uploadZone.style.borderColor = '';
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.style.background = '';
        uploadZone.style.borderColor = '';
        
        if (e.dataTransfer.files.length > 0) {
            videoFile.files = e.dataTransfer.files;
            handleFile(e.dataTransfer.files[0]);
        }
    });

    // 3. ОБРАБОТКА ФАЙЛА
    function handleFile(file) {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        
        fileName.textContent = file.name;
        fileMeta.textContent = `${sizeMB} MB`;
        fileInfo.style.display = 'block';
        
        // ПРОВЕРКА РАЗМЕРА
        if (file.size > 500 * 1024 * 1024) {
            alert('⚠️ Файл слишком большой! Максимальный размер: 500MB');
            videoFile.value = '';
            fileInfo.style.display = 'none';
        }
    }

    // 4. ОБНОВЛЕНИЕ ПРОГРЕССА
    function updateProgress(percent, text) {
        if (progressFill) progressFill.style.width = percent + '%';
        if (progressPercent) progressPercent.textContent = percent + '%';
        if (progressText) progressText.textContent = text;
    }

    // 5. ПОКАЗ РЕЗУЛЬТАТОВ
    function showResults(data) {
        if (!resultGrid) return;
        
        resultGrid.innerHTML = `
            <div class="result-card">
                <div class="result-label">Видео ID</div>
                <div class="result-value">${data.video_id || 'Н/Д'}</div>
            </div>
            <div class="result-card">
                <div class="result-label">Анализ ID</div>
                <div class="result-value">${data.analysis_id || 'Н/Д'}</div>
            </div>
            <div class="result-card">
                <div class="result-label">Животное</div>
                <div class="result-value">${data.animal_name || 'Авто'}</div>
            </div>
            <div class="result-card">
                <div class="result-label">Диагноз</div>
                <div class="result-value">${data.diagnosis || 'Норма'}</div>
            </div>
            <div class="result-card">
                <div class="result-label">Хромота</div>
                <div class="result-value" style="color: ${data.is_lame ? '#dc3545' : '#28a745'}">
                    ${data.is_lame ? 'ДА ⚠️' : 'НЕТ ✅'}
                </div>
            </div>
        `;
        
        if (progressSection) progressSection.style.display = 'none';
        if (resultSection) resultSection.style.display = 'block';
    }

    // 6. ОБРАБОТКА ФОРМЫ (УПРОЩЕННАЯ)
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('📤 Отправка формы...');
        
        // ПРОВЕРКИ
        const animalSelect = document.getElementById('animalSelect');
        if (!animalSelect || !animalSelect.value) {
            alert('❌ Пожалуйста, выберите животное');
            if (animalSelect) animalSelect.focus();
            return;
        }
        
        if (!videoFile.files.length) {
            alert('❌ Пожалуйста, выберите видеофайл');
            return;
        }
        
        // ПОДГОТОВКА
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span>⏳</span><span>Загрузка...</span>';
        }
        if (progressSection) {
            progressSection.style.display = 'block';
        }
        updateProgress(25, 'Загрузка файла на сервер...');
        
        try {
            // ПРОСТОЙ ЗАПРОС БЕЗ CSRF (для теста)
            const formData = new FormData(this);
            
            console.log('Отправка на /api/upload/simple/');
            const response = await fetch('/api/upload/simple/', {
                method: 'POST',
                body: formData
            });
            
            console.log('Статус ответа:', response.status);
            
            // Пробуем получить текст ответа
            const responseText = await response.text();
            console.log('Текст ответа:', responseText.substring(0, 200));
            
            let data;
            try {
                data = JSON.parse(responseText);
            } catch (parseError) {
                console.error('Ошибка парсинга JSON:', parseError);
                throw new Error('Сервер вернул некорректный ответ');
            }
            
            if (data.success) {
                updateProgress(100, '✅ Анализ завершен!');
                
                // Показываем результат
                setTimeout(() => {
                    showResults(data);
                    
                    // Перенаправление через 3 секунды
                    setTimeout(() => {
                        window.location.href = '/analysis/results/';
                    }, 3000);
                }, 1000);
                
            } else {
                throw new Error(data.error || 'Ошибка сервера');
            }
            
        } catch (error) {
            console.error('❌ Ошибка загрузки:', error);
            
            // ВОССТАНОВЛЕНИЕ
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span>🚀</span><span>Запустить ML анализ</span>';
            }
            if (progressSection) progressSection.style.display = 'none';
            
            alert('❌ Ошибка: ' + error.message);
        }
    });
    
    // ИНИЦИАЛИЗАЦИЯ
    console.log('✅ Интерфейс готов к работе');
});
</script>
