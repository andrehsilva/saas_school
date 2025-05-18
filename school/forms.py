# school/forms.py
from django import forms
from school.models import GradeCoordinator

class ImportCSVForm(forms.Form):
    csv_file = forms.FileField(label="Arquivo CSV")




class GradeCoordinatorForm(forms.ModelForm):
    class Meta:
        model = GradeCoordinator
        fields = '__all__'
        widgets = {
            'grade': forms.Select(attrs={'class': 'grade-select'})  # Força seleção
        }