# backend/ml/apps.py
# Django app configuration to load ML model on startup

from django.apps import AppConfig


class MlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml'
    verbose_name = 'Machine Learning'

    def ready(self):
        """
        Called when Django starts.
        This is where we load the ML model.
        """
        # Import and load the model
        from . import views
        print("🤖 Loading ML model on Django startup...")
        views.load_model()
        print("✅ ML module ready!")