import sys
from django.apps import AppConfig

class SharedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shared'

    def ready(self):
        # ❗ Skip loading signals during migrations
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return
        
        import shared.signals
        print("✅ Signals loaded for shared app")
