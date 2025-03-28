from django import forms
from .models import Contato
import re

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contato
        fields = ['name', 'email', 'phone', 'mensage']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Digite seu nome', 'class': 'w-full p-2 border rounded'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Informe seu melhor e-mail', 'class': 'w-full p-2 border rounded'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Digite seu telefone, exemplo 16999999999', 'class': 'w-full p-2 border rounded'}),
            'mensage': forms.Textarea(attrs={'placeholder': 'Escreva sua mensagem, detalhe seu contato.', 'class': 'w-full p-2 border rounded h-32'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')

        # Remover espaços e caracteres não numéricos
        phone = re.sub(r'\D', '', phone)

        # Verificar se o telefone tem entre 9 e 15 dígitos
        if len(phone) < 9 or len(phone) > 15:
            raise forms.ValidationError("O telefone deve ter entre 9 e 15 dígitos.")

        return phone
