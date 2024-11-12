import pytest
from django.utils import timezone
from core.tasks import process_unprocessed_events
from core.models import Outbox
from users.use_cases import CreateUser, CreateUserRequest

@pytest.mark.django_db
def test_create_user_with_outbox_logging():
    use_case = CreateUser()
    request = CreateUserRequest(email="test@email.com", first_name="Test", last_name="Test")
    
    response = use_case.execute(request)
    
    assert response.result.email == "test@email.com"
    assert Outbox.objects.filter(event_type="user_created", processed=False).count() == 1

@pytest.mark.django_db
def test_process_unprocessed_events():
    events = [
        Outbox(
            event_type="user_created",
            event_date_time=timezone.now(),
            environment="Local",
            event_context={"user_id": i, "action": "created"},
            metadata_version=1,
            processed=False,
        )
        for i in range(10)
    ]
    Outbox.objects.bulk_create(events)    
    process_unprocessed_events()    
    assert Outbox.objects.filter(processed=True).count() == 10
