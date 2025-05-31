from django import forms
from .models import Blog, Category

class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = [
            'name', 'image', 'short_description', 'description',
            'categories', 'star', 'active'
        ]
        widgets = {
            'categories': forms.SelectMultiple(attrs={'class': 'select2 w-full'}),
            'description': forms.Textarea(attrs={'rows': 8}),
            'short_description': forms.Textarea(attrs={'rows': 3}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }