from django import forms
from web.database.models import Animal, User

class VideoUploadForm(forms.Form):
    """Форма для загрузки видео"""
    
    animal = forms.ModelChoiceField(
        queryset=Animal.objects.none(),
        label="Выберите животное",
        required=True,
        empty_label="-- Выберите животное --",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'animalSelect'
        })
    )
    
    video_file = forms.FileField(
        label="Видеофайл",
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'id': 'videoFile',
            'accept': '.mp4,.avi,.mov,.mkv,.webm',
            'style': 'display: none;'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            try:
                custom_user = User.objects.get(login=user.username)
                self.fields['animal'].queryset = Animal.objects.filter(user=custom_user)
            except:
                self.fields['animal'].queryset = Animal.objects.none()

class AnimalForm(forms.Form):
    """Форма для добавления животного"""
    
    name = forms.CharField(
        label="Кличка",
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите кличку лошади'
        })
    )
    
    sex = forms.ChoiceField(
        label="Пол",
        choices=[('', '-- Выберите пол --'), ('M', 'Жеребец'), ('F', 'Кобыла'), ('G', 'Мерин')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    age = forms.IntegerField(
        label="Возраст (лет)",
        required=False,
        min_value=0,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Возраст'
        })
    )
    
    weight = forms.FloatField(
        label="Вес (кг)",
        required=False,
        min_value=100,
        max_value=1000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Примерный вес',
            'step': '0.1'
        })
    )
