from rest_framework import serializers
from .models import LegalDocument

class LegalDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalDocument
        fields = ['id', 'title', 'file', 'uploaded_at', 'is_processed', 'processing_error']
        read_only_fields = ['id', 'uploaded_at', 'is_processed', 'processing_error']