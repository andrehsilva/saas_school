from django.apps import AppConfig


class AUsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'a_users'
    verbose_name = 'Perfis'
    
    def ready(self):
        import a_users.signals
