from celery import Celery
from django.conf import settings
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.beat_schedule = {
    "process-outbox-every-minute": {
        "task": "logs.tasks.process_outbox_task",
        "schedule": 60.0,  
        "args": (settings.LOG_BATCH_SIZE,), 
    },
}
