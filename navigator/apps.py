from django.apps import AppConfig


class NavigatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'navigator'
    verbose_name = 'Gerenciar Links/Apps'

    
    def ready(self):
        import navigator.signals 