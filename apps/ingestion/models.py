import os
import uuid
from django.db import models

def upload_to(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('raw_pdfs', filename)

class LegalDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to=upload_to)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title or str(self.id)

    def save(self, *args, **kwargs):
        if not self.title and self.file:
            self.title = self.file.name
        super().save(*args, **kwargs)