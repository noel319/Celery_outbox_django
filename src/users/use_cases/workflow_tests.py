import pytest
from django.utils import timezone
from celery.exceptions import MaxRetriesExceededError
from users.models import Outbox
from core.tasks import push_to_clickhouse
import uuid
from unittest.mock import patch
from core.batch_insert import batch_insert_events
from typing import List, Dict
from unittest.mock import MagicMock

pytestmark = pytest.mark.django_db

def test_event_creation_in_outbox() -> None:
    event_data_list = generate_test_events(5000)
    batch_insert_events(event_data_list)
    assert Outbox.objects.filter(processed=False).count() == 5000

@patch("core.event_log_client.EventLogClient.insert")
def test_push_events_to_clickhouse(mock_insert:MagicMock) -> None:    
    event_data_list = generate_test_events(1000)
    batch_insert_events(event_data_list)
    mock_insert.side_effect = Exception("ClickHouse connection error")
    push_to_clickhouse.delay()    
    processed_events = Outbox.objects.filter(processed=True).count()
    assert processed_events == 0

@patch("core.event_log_client.EventLogClient.insert")
def test_push_events_with_retry(mock_insert:MagicMock) -> None:    
    event_data_list = generate_test_events(1000)
    batch_insert_events(event_data_list)
    mock_insert.side_effect = Exception("ClickHouse connection error")
    with patch("sentry_sdk.capture_exception"):  
        try:
            push_to_clickhouse.delay()
        except MaxRetriesExceededError:
            pass   
    unprocessed_events = Outbox.objects.filter(processed=False).count()
    assert unprocessed_events == 1000    
    


def generate_test_events(count: int) -> List[Dict]:    
    return [
        {
            "event_type": "user_action",
            "event_date_time": timezone.now(),
            "environment": "test",
            "event_context": {"user_id": str(uuid.uuid4()), "action": "test_action"},
            "metadata_version": 1
        }
        for _ in range(count)
    ]

def test_batch_insert_events() -> None:    
    events = generate_test_events(5000)   
    batch_insert_events(events, batch_size=1000)    
    assert Outbox.objects.count() == 5000
    assert Outbox.objects.filter(processed=False).count() == 5000
