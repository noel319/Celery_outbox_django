from django.db import models
from django.utils.timezone import now

class OutboxLog(models.Model):
    event_type = models.CharField(max_length=255)
    event_date_time = models.DateTimeField(default=now)
    environment = models.CharField(max_length=255)
    event_context = models.JSONField()
    metadata_version = models.PositiveIntegerField(default=1)
    processed = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["processed", "event_date_time"]),
        ]
