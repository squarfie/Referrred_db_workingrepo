from django.apps import AppConfig

class WgsAppConfig(AppConfig):
    name = 'apps.wgs_app'

    def ready(self):
        import apps.wgs_app.signals  # <-- ensures signal registration
