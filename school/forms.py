# school/forms.py
from django import forms

class ImportCSVForm(forms.Form):
    csv_file = forms.FileField(label="Arquivo CSV")
