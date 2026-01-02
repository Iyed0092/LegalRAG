from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import LegalDocument
from .serializers import LegalDocumentSerializer
from .services.loader import process_document

class LegalDocumentViewSet(viewsets.ModelViewSet):
    queryset = LegalDocument.objects.all()
    serializer_class = LegalDocumentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        print(f"Starting RAG pipeline for: {instance.title}")
        process_document(instance.file.path, instance.title)
        instance.is_processed = True
        instance.processing_error = ""
        instance.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "Document ingested and indexed successfully!",
                "data": LegalDocumentSerializer(instance).data
            }, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )
