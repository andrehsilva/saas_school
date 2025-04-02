from django.apps import AppConfig


class SchoolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'school'
    verbose_name = 'Gestão de estrutura escolar'

    def ready(self):
        import school.signals  # Importa os signals para garantir que eles sejam registrados
