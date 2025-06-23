from django import forms
from .models import Note

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = [
            'student', 'subject', 'title', 'description', 'performance',
            'score', 'weight', 'date', 'evaluation_period', 'attachment'
        ]
        widgets = {
            'date': forms.DateInput(format='%d/%m/%Y'), 
            'description': forms.Textarea(attrs={'rows': 3}),
            'performance': forms.Textarea(attrs={'rows': 3}),
        }