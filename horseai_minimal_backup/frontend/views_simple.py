"""
Упрощенные views для быстрого запуска
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from web.database.models import Animal, User

@login_required
def simple_ration(request):
    """Упрощенная страница расчета рациона"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        animals = Animal.objects.filter(user=custom_user)
    except:
        animals = []
    
    return render(request, 'frontend/ration.html', {'animals': animals})
