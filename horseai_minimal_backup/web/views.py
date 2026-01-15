# Пустой views.py чтобы избежать ошибок импорта


from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def ration_list_view(request):
    """Отображение списка рационов"""
    return render(request, 'ration/list.html')

def public_rations_api_view(request):
    """Публичная страница API документации"""
    return render(request, 'ration/api_info.html')
