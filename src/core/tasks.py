import json
from celery import shared_task
from users.models import Outbox
from core.event_log_client import EventLogClient
import structlog
import sentry_sdk
from sentry_sdk import capture_exception
from sentry_sdk import start_transaction

logger = structlog.get_logger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def push_to_clickhouse(self) -> None:
    try:
        with start_transaction(op="task", name="push_to_clickhouse"):         
            events = Outbox.objects.filter(processed=False)
            if not events.exists():
                return

            
            event_ids = list(events.values_list('id', flat=True)[:1000])  
            data = [
                {
                    "event_type": event.event_type,
                    "event_date_time": event.event_date_time,
                    "environment": event.environment,
                    "event_context": json.dumps(event.event_context),
                    "metadata_version": event.metadata_version
                }
                for event in events.filter(id__in=event_ids)
            ]

            
            with EventLogClient.init() as client:
                
                try:
                    client.insert(data=data)  
                except Exception as e:
                    logger.error(f"Failed to insert data into ClickHouse: {e}")
                    raise  

            
            Outbox.objects.filter(id__in=event_ids).update(processed=True)
            logger.info("Successfully pushed events to ClickHouse", event_count=len(data))

    except Exception as e:
        capture_exception(e)  
        logger.error("Failed to push events to ClickHouse", error=str(e))
        raise  
