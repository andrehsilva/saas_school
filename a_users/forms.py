from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User
from .models import Profile

class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'displayname', 'info', 'phone','cpf' ]
        widgets = {
            'image': forms.FileInput(),
            'displayname' : forms.TextInput(attrs={'placeholder': 'Add display name'}),
            'cpf': forms.TextInput(attrs={'placeholder': 'Enter your CPF'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
            'info' : forms.Textarea(attrs={'rows':3, 'placeholder': 'Add information'})
        }
        
    # Validação personalizada para o CPF, caso precise de algo adicional
    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        # Se houver algum validador ou lógica adicional de CPF, adicione aqui
        # Exemplo:
        if len(cpf) != 11:  # Apenas exemplo, ajuste conforme sua validação real
            raise forms.ValidationError("CPF must have 11 digits")
        return cpf
    

class EmailForm(ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email']


class UsernameForm(ModelForm):
    class Meta:
        model = User
        fields = ['username']
