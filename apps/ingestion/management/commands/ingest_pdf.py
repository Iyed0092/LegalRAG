import os
from django.core.management.base import BaseCommand
from apps.ingestion.services.loader import DocumentLoader

class Command(BaseCommand):
    help = 'Ingests a PDF file into Neo4j and ChromaDB using the GraphRAG pipeline'

    def add_arguments(self, parser):
        # On définit l'argument qui acceptera le chemin du fichier
        parser.add_argument('file_path', type=str, help='Absolute path to the PDF file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        
        # 1. Vérification que le fichier existe
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"❌ File not found: {file_path}"))
            return

        filename = os.path.basename(file_path)
        self.stdout.write(self.style.SUCCESS(f"🚀 Starting ingestion for {filename}..."))

        # 2. Appel de ton service Loader
        loader = DocumentLoader()
        
        # On appelle la fonction que tu as codée
        success = loader.process_and_load(file_path, filename)

        # 3. Résultat
        if success:
            self.stdout.write(self.style.SUCCESS(f"✅ Successfully ingested {filename}"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Ingestion failed for {filename} (Check Docker logs for details)"))