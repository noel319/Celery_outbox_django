from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.db.models import JSONField
from core.models import TimeStampedModel
from django.utils import timezone

class User(TimeStampedModel, AbstractBaseUser):
    email = models.EmailField(unique=True, db_index=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'

    class Meta(AbstractBaseUser.Meta):
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self) -> str:
        if all([self.first_name, self.last_name]):
            return f'{self.first_name} {self.last_name}'

        return self.email
class Outbox(models.Model):
    event_type = models.CharField(max_length=255)
    event_date_time = models.DateTimeField(default=timezone.now)
    environment = models.CharField(max_length=255)
    event_context = JSONField()
    metadata_version = models.BigIntegerField(default=1)
    processed = models.BooleanField(default=False)

    class Meta:
        db_table = 'outbox'
        indexes = [
            models.Index(fields=['processed']),
        ]