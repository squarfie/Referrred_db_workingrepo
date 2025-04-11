from django.apps import AppConfig


class EgaspAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.home'


    def ready(self):
        from django.utils.module_loading import autodiscover_modules
        autodiscover_modules('signals') #find signals.py