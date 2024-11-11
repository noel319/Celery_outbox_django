from django.contrib.auth.models import AbstractBaseUser
from django.db import models

from core.models import TimeStampedModel


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
