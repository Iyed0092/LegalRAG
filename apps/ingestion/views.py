from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import LegalDocument
from .serializers import LegalDocumentSerializer

from .services.loader import process_document 

class LegalDocumentViewSet(viewsets.ModelViewSet):
    queryset = LegalDocument.objects.all().order_by('-uploaded_at')
    serializer_class = LegalDocumentSerializer

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        document = self.get_object()
        
        if document.is_processed:
            return Response(
                {"status": "Document already processed"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            process_document(document.file.path, document.title)
            
            document.is_processed = True
            document.save()
            return Response({"status": "Processing started"}, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            document.processing_error = str(e)
            document.save()
            print(f" ERREUR LORS DU PROCESSING : {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)