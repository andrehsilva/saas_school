# school/forms.py
from django import forms
from school.models import Grade


class ImportCSVForm(forms.Form):
    csv_file = forms.FileField(label="Arquivo CSV")




class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['name', 'coordinators', 'directors', 'colaborator']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full bg-gray-50'}),
            'coordinators': forms.SelectMultiple(attrs={'class': 'select select-bordered w-full bg-gray-50'}),
            'directors': forms.SelectMultiple(attrs={'class': 'select select-bordered w-full bg-gray-50'}),
            'colaborator': forms.SelectMultiple(attrs={'class': 'select select-bordered w-full bg-gray-50'}),
        }