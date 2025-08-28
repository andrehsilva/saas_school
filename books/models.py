from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from school.models import Grade, Class

class Category(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nome"),
        help_text=_("Nome da categoria (ex: Literatura, Ciências, História).")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Categoria")
        verbose_name_plural = _("Categorias")


class Document(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name=_("Título"),
        help_text=_("Título do livro ou documento.")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Descrição"),
        help_text=_("Descrição opcional sobre o conteúdo do documento.")
    )
    file = models.FileField(
        upload_to='books/pdfs/',
        verbose_name=_("Arquivo"),
        help_text=_("Arquivo PDF do livro ou documento.")
    )
    thumbnail = models.ImageField(
        upload_to='books/pdfs/thumbs/',
        blank=True,
        null=True,
        verbose_name=_("Miniatura"),
        help_text=_("Imagem de capa ou visualização do documento.")
    )
    categories = models.ManyToManyField(
        Category,
        blank=True,
        verbose_name=_("Categorias"),
        help_text=_("Categorias associadas ao documento.")
    )
    target_grades = models.ManyToManyField(
        Grade,
        blank=True,
        related_name='documents',
        verbose_name=_("Séries Alvo"),
        help_text=_("Séries escolares para as quais o documento é destinado.")
    )
    target_classes = models.ManyToManyField(
        Class,
        blank=True,
        related_name='documents',
        verbose_name=_("Classes Alvo"),
        help_text=_("Classes específicas que devem receber o documento.")
    )
    target_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='individual_documents',
        verbose_name=_("Usuários Alvo"),
        help_text=_("Usuários específicos que devem receber o documento.")
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents',
        verbose_name=_("Enviado por"),
        help_text=_("Usuário responsável pelo envio do documento.")
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Data de Envio"),
        help_text=_("Data e hora em que o documento foi enviado.")
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Livro-Documento")
        verbose_name_plural = _("Livros-Documentos")


class ReceivedDocument(models.Model):
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_documents",
        verbose_name=_("Destinatário"),
        help_text=_("Usuário que recebeu o documento.")
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="received_by",
        verbose_name=_("Documento"),
        help_text=_("Documento recebido pelo usuário.")
    )
    read = models.BooleanField(
        default=False,
        verbose_name=_("Lido"),
        help_text=_("Indica se o documento foi lido pelo destinatário.")
    )
    received_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Data de Recebimento"),
        help_text=_("Data em que o documento foi disponibilizado ao usuário.")
    )

    def __str__(self):
        return f"{self.recipient.username} - {self.document.title}"

    class Meta:
        verbose_name = _("Recebido")
        verbose_name_plural = _("Recebidos")


class DocumentReadLog(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Usuário"),
        help_text=_("Usuário que leu o documento.")
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        verbose_name=_("Documento"),
        help_text=_("Documento que foi lido.")
    )
    read = models.BooleanField(
        default=True,
        verbose_name=_("Lido"),
        help_text=_("Indica se o documento foi lido (valor padrão: True).")
    )
    read_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Data de Leitura"),
        help_text=_("Data e hora da leitura do documento.")
    )

    class Meta:
        verbose_name = _("Log de Leitura")
        verbose_name_plural = _("Logs de Leitura")
        unique_together = ('user', 'document')
