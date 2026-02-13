from django.apps import AppConfig

class HomeFinalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.home_final'

    def ready(self):
        import apps.home_final.signals  
