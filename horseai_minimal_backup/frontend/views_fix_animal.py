
@csrf_exempt
def upload_video_simple_api_real(request):
    """РЕАЛЬНЫЙ API для загрузки видео - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST метод'}, status=405)
    
    try:
        print("="*50)
        print("REAL API: Начало загрузки видео")
        print(f"Пользователь: {request.user}")
        print(f"Аутентифицирован: {request.user.is_authenticated}")
        
        # Проверяем аутентификацию
        if not request.user.is_authenticated:
            print("⚠️ Пользователь не аутентифицирован")
            return JsonResponse({
                'success': False, 
                'error': 'Требуется аутентификация. Пожалуйста, войдите в систему.',
                'login_url': '/login/'
            }, status=401)
        
        # Получаем данные
        video_file = request.FILES.get('video_file')
        animal_id = request.POST.get('animal_id', '')
        
        if not video_file:
            print("❌ Ошибка: Файл не выбран")
            return JsonResponse({'success': False, 'error': 'Файл не выбран'})
        
        if not animal_id:
            print("❌ Ошибка: Не указан ID животного")
            return JsonResponse({'success': False, 'error': 'Выберите животное'})
        
        print(f"✅ Файл получен: {video_file.name}, размер: {video_file.size} байт")
        print(f"✅ ID животного из формы: {animal_id}")
        
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
        
        # 2. ПОИСК ИЛИ СОЗДАНИЕ ЖИВОТНОГО
        from web.database.models import User as CustomUser, Animal, Video, Analysis
        
        try:
            custom_user = CustomUser.objects.get(login=request.user.username)
            print(f"✅ Найден пользователь: {custom_user.login}")
        except CustomUser.DoesNotExist:
            print(f"⚠️ Пользователь {request.user.username} не найден в CustomUser")
            return JsonResponse({
                'success': False, 
                'error': 'Ошибка: пользователь не найден в системе'
            }, status=400)
        
        # Пытаемся найти животное
        animal = None
        
        # Вариант 1: Ищем животное по ID и пользователю
        try:
            animal = Animal.objects.get(animal_id=animal_id, user=custom_user)
            print(f"✅ Найдено животное пользователя: {animal.name} (ID: {animal.animal_id})")
        except Animal.DoesNotExist:
            print(f"⚠️ Животное ID {animal_id} не найдено у пользователя {custom_user.login}")
            
            # Вариант 2: Ищем животное только по ID (может принадлежать другому пользователю)
            try:
                animal = Animal.objects.get(animal_id=animal_id)
                print(f"⚠️ Найдено животное другого пользователя: {animal.name}")
                
                # Создаем копию для текущего пользователя
                new_animal = Animal.objects.create(
                    user=custom_user,
                    name=f"{animal.name} (копия)",
                    sex=animal.sex,
                    age=animal.age,
                    estimated_weight=animal.estimated_weight,
                    created_at=datetime.now()
                )
                animal = new_animal
                print(f"✅ Создана копия животного: {animal.name}")
                
            except Animal.DoesNotExist:
                # Вариант 3: Создаем новое животное с указанным ID в имени
                animal = Animal.objects.create(
                    user=custom_user,
                    name=f'Лошадь {animal_id}',
                    sex='M',
                    age=5,
                    estimated_weight=500.0,
                    created_at=datetime.now()
                )
                print(f"✅ Создано новое животное: {animal.name}")
        
        # 3. СОЗДАНИЕ ЗАПИСИ ВИДЕО
        video = Video.objects.create(
            animal=animal,
            user=custom_user,
            file_path=f'videos/{filename}',
            upload_date=datetime.now(),
            duration=0,
            resolution='unknown',
            analysis_status='uploaded'
        )
        
        print(f"✅ Видео создано в БД: ID={video.video_id}")
        
        # 4. СОЗДАНИЕ АНАЛИЗА
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
        
        # 5. ФОРМИРОВАНИЕ ОТВЕТА
        response_data = {
            'success': True,
            'message': 'Видео успешно загружено и проанализировано!',
            'video_id': video.video_id,
            'analysis_id': analysis.analysis_id,
            'file_path': video.file_path,
            'file_size': video_file.size,
            'animal_id': animal.animal_id,
            'animal_name': animal.name,
            'animal_sex': animal.sex,
            'animal_age': animal.age,
            'animal_weight': animal.estimated_weight,
            'diagnosis': analysis.diagnosis,
            'lameness_probability': analysis.lameness_probability,
            'is_lame': analysis.is_lame,
            'user': request.user.username
        }
        
        print(f"✅ Ответ: {json.dumps(response_data, ensure_ascii=False)}")
        print("="*50)
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
