import os
from django.conf import settings
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core", broker=settings.CELERY_BROKER)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.update(
    broker_connection_retry_on_startup=True,    
)
app.conf.beat_schedule = {
    'push-to-clickhouse-every-minute': {
        'task': 'core.tasks.push_to_clickhouse',
        'schedule': crontab(minute='*/1'),  # every 1 minute
    },
}
