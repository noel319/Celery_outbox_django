import json
from celery import shared_task
from users.models import Outbox
from core.event_log_client import EventLogClient
import structlog
from django.db import transaction



logger = structlog.get_logger(__name__)

def process_unprocessed_events():
    event_ids = list(Outbox.objects.filter(processed=False).values_list("id", flat=True)[:1000])
    events = Outbox.objects.filter(id__in=event_ids)
    data = [
        {
            "event_type": event.event_type,
            "event_date_time": event.event_date_time,
            "environment": event.environment,
            "event_context": json.dumps(event.event_context),
            "metadata_version": event.metadata_version
        }
        for event in events
    ]
    logger.info("Preparing data for ClickHouse insertion", data=data)
    with transaction.atomic():
        with EventLogClient.init() as client:
            client.insert(data=data)
            logger.info("Data pushed to ClickHouse", event_count=len(data))
        events.update(processed=True)
        logger.info("Successfully pushed events to ClickHouse", event_count=len(data))

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def push_to_clickhouse(self):
    try:
        process_unprocessed_events()
    except Exception as e:
        logger.error("Failed to push events to ClickHouse", error=str(e))
        raise