"""
Views для истории рационов
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from web.database.models import Animal, User

@login_required
def ration_history_view(request):
    """Страница истории рационов"""
    try:
        custom_user = User.objects.get(login=request.user.username)
        animals = Animal.objects.filter(user=custom_user)
    except:
        animals = []
    
    return render(request, 'frontend/ration_history.html', {'animals': animals})
