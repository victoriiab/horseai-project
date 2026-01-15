"""
Views для работы с рационами
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from web.database.models import Animal, Ration, User

@login_required
def rations_history(request):
    """Страница истории рационов пользователя"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        
        # Получаем животных пользователя
        user_animals = Animal.objects.filter(user=custom_user)
        
        # Получаем рационы
        rations = Ration.objects.filter(animal__in=user_animals).order_by('-calculation_date')
        
        context = {
            'rations': rations,
            'animals': user_animals,
            'total_count': rations.count()
        }
        
        return render(request, 'frontend/rations_history.html', context)
        
    except Exception as e:
        # Если ошибка, показываем пустую страницу
        return render(request, 'frontend/rations_history.html', {
            'rations': [],
            'animals': [],
            'total_count': 0,
            'error': str(e)
        })
