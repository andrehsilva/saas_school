from django.db import models
from django.contrib.auth.models import User
from school.models import Grade, Class

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"



class Document(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='books/pdfs/')
    categories = models.ManyToManyField(Category, blank=True)
    thumbnail = models.ImageField(upload_to='books/pdfs/thumbs/', blank=True, null=True)
    target_grades = models.ManyToManyField(Grade, blank=True, related_name='documents')
    target_classes = models.ManyToManyField(Class, blank=True, related_name='documents')
    target_users = models.ManyToManyField(User, blank=True, related_name='individual_documents')

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Livro-Documento"
        verbose_name_plural = "Livros-Documentos"


class ReceivedDocument(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_documents")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="received_by")
    read = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient.username} - {self.document.title}"


class DocumentReadLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    read = models.BooleanField(default=True)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'document')
