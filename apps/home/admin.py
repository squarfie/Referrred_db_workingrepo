from django.contrib import admin
from django.apps import apps

# Get all models from the current app
app = apps.get_app_config('home')

# Register each model with the admin site
for model_name, model in app.models.items():
    admin.site.register(model)

