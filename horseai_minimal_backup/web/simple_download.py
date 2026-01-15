from django.http import FileResponse, HttpResponse
import glob
import os

def download_latest_annotated(request):
    """Скачать последнее размеченное видео"""
    # Ищем последний файл
    video_files = glob.glob("/home/ais/shared/horseAI/data/output/*labeled*.mp4")
    
    if not video_files:
        return HttpResponse("Нет размеченных видео", status=404)
    
    # Берем последнее по времени изменения
    latest_video = max(video_files, key=os.path.getmtime)
    
    response = FileResponse(open(latest_video, 'rb'))
    response['Content-Type'] = 'video/mp4'
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(latest_video)}"'
    
    return response

def simple_download_page(request):
    """Простая страница для скачивания"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head><title>Скачать размеченное видео</title></head>
    <body>
        <h1>📥 Скачать размеченное видео</h1>
        
        <h3>Последние видео:</h3>
        <ul>
    '''
    
    import glob
    videos = glob.glob("/home/ais/shared/horseAI/data/output/*labeled*.mp4")
    videos.sort(key=os.path.getmtime, reverse=True)
    
    for video in videos[:10]:  # Последние 10
        filename = os.path.basename(video)
        size_mb = os.path.getsize(video) / (1024*1024)
        html += f'''
            <li>
                <a href="/download-annotated-file/?file={filename}">
                    {filename}
                </a> ({size_mb:.1f} MB)
            </li>
        '''
    
    html += '''
        </ul>
        
        <h3>Или скачать последнее:</h3>
        <a href="/download-latest-annotated/" style="
            display: inline-block;
            background: #4CAF50;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-size: 18px;
        ">
            📥 Скачать последнее размеченное видео
        </a>
    </body>
    </html>
    '''
    
    return HttpResponse(html)

def download_by_filename(request):
    """Скачать по имени файла"""
    filename = request.GET.get('file', '')
    if not filename:
        return HttpResponse("Укажите параметр file", status=400)
    
    video_path = f"/home/ais/shared/horseAI/data/output/{filename}"
    
    if not os.path.exists(video_path):
        return HttpResponse(f"Файл не найден: {filename}", status=404)
    
    response = FileResponse(open(video_path, 'rb'))
    response['Content-Type'] = 'video/mp4'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
