from django.db import transaction
from core.models import Outbox
import logging

logger = logging.getLogger(__name__)

def batch_insert_events(event_data_list, batch_size=1000):
    batches = [
        event_data_list[i:i + batch_size] for i in range(0, len(event_data_list), batch_size)
    ]
    for batch in batches:
        outbox_events = [
            Outbox(
                event_type=event['event_type'],
                event_date_time=event['event_date_time'],
                environment=event['environment'],
                event_context=event['event_context'],
                metadata_version=event['metadata_version'],
                processed=False,
            ) for event in batch
        ]

        with transaction.atomic():
            Outbox.objects.bulk_create(outbox_events, batch_size=batch_size)
        logger.info(f"Inserted {len(batch)} events into the outbox.")