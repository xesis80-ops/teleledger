import os
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # RUN_MAIN guard avoids double-start under the Django dev server's autoreloader
        if os.environ.get("RUN_MAIN") == "true" or os.environ.get("DJANGO_DEBUG") != "True":
            from .scheduler import start_scheduler
            try:
                start_scheduler()
            except Exception:
                pass  # DB may not be migrated yet during initial deploy steps
