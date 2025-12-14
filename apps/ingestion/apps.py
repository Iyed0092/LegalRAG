from django.apps import AppConfig

class IngestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ingestion'  # ⚠️ Doit être 'apps.ingestion', pas juste 'ingestion'