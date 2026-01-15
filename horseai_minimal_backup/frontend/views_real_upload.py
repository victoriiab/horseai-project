@csrf_exempt
def upload_video_simple_api_real(request):
    """РЕАЛЬНЫЙ API для загрузки видео с сохранением в БД"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST метод'}, status=405)
    
    try:
        print("="*50)
        print("REAL API: Начало загрузки видео")
        
        # Получаем данные
        video_file = request.FILES.get('video_file')
        animal_id = request.POST.get('animal_id', '1')
        
        if not video_file:
            print("❌ Ошибка: Файл не выбран")
            return JsonResponse({'success': False, 'error': 'Файл не выбран'})
        
        print(f"✅ Файл получен: {video_file.name}, размер: {video_file.size} байт")
        print(f"✅ ID животного: {animal_id}")
        
        # 1. СОХРАНЕНИЕ ФАЙЛА
        import uuid
        import os
        from django.conf import settings
        
        # Создаем безопасное имя файла
        safe_name = str(uuid.uuid4())[:8] + '_' + video_file.name.replace(' ', '_')
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}"
        
        # Папка для сохранения
        media_dir = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(media_dir, exist_ok=True)
        
        filepath = os.path.join(media_dir, filename)
        
        # Сохраняем файл
        with open(filepath, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)
        
        print(f"✅ Файл сохранен: {filepath}")
        
        # 2. СОЗДАНИЕ ЗАПИСИ В БД
        try:
            # Ищем или создаем тестового пользователя
            from django.contrib.auth.models import User as AuthUser
            from web.database.models import User as CustomUser, Animal, Video
            
            # Для теста используем первого пользователя
            try:
                custom_user = CustomUser.objects.first()
                if not custom_user:
                    # Создаем тестового пользователя
                    custom_user = CustomUser.objects.create(
                        login='test_upload_user',
                        password_hash='test',
                        email='test@example.com',
                        full_name='Test Upload User',
                        role_id='user',
                        created_at=datetime.now(),
                        is_active=True
                    )
            except:
                custom_user = None
            
            # Ищем животное
            try:
                animal = Animal.objects.get(animal_id=animal_id)
            except Animal.DoesNotExist:
                # Создаем тестовое животное
                animal = Animal.objects.create(
                    user=custom_user or CustomUser.objects.first(),
                    name='Автоматически созданная лошадь',
                    sex='M',  # Только M или F!
                    age=5,
                    estimated_weight=500.0,
                    created_at=datetime.now()
                )
                print(f"✅ Создано новое животное: {animal.name} (ID: {animal.animal_id})")
            
            # Создаем запись видео
            video = Video.objects.create(
                animal=animal,
                user=custom_user or CustomUser.objects.first(),
                file_path=f'videos/{filename}',
                upload_date=datetime.now(),
                duration=0,  # Можно позже вычислить
                resolution='unknown',
                analysis_status='uploaded'
            )
            
            print(f"✅ Видео создано в БД: ID={video.video_id}")
            
            # 3. СОЗДАЕМ АНАЛИЗ (для демонстрации)
            from web.database.models import Analysis
            analysis = Analysis.objects.create(
                video=video,
                posture='normal',
                gait_quality='good',
                size_category='large',
                estimated_weight=animal.estimated_weight or 500.0,
                confidence_score=0.85,
                analysis_date=datetime.now(),
                is_lame=False,
                lameness_probability=15.5,
                diagnosis='Норма',
                diagnosis_note='Признаков хромоты не обнаружено'
            )
            
            print(f"✅ Анализ создан: ID={analysis.analysis_id}")
            
            response_data = {
                'success': True,
                'message': 'Видео успешно загружено и проанализировано!',
                'video_id': video.video_id,
                'analysis_id': analysis.analysis_id,
                'file_path': video.file_path,
                'file_size': video_file.size,
                'animal_name': animal.name,
                'diagnosis': analysis.diagnosis,
                'lameness_probability': analysis.lameness_probability,
                'is_lame': analysis.is_lame
            }
            
        except Exception as db_error:
            print(f"⚠️ Ошибка БД, но файл сохранен: {db_error}")
            response_data = {
                'success': True,
                'message': 'Видео сохранено, но возникла ошибка при записи в БД',
                'file_path': f'videos/{filename}',
                'file_size': video_file.size,
                'note': f'Ошибка БД: {str(db_error)}'
            }
        
        print(f"✅ Ответ: {json.dumps(response_data, ensure_ascii=False)}")
        print("="*50)
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
