import uuid
import json
from unittest.mock import ANY
import pytest
from clickhouse_connect import get_client
from django.conf import settings
from users.use_cases import CreateUser, CreateUserRequest, UserCreated
from logs.models import OutboxLog
from logs.services import process_logs
import datetime
pytestmark = [pytest.mark.django_db]


@pytest.fixture()
def f_use_case() -> CreateUser:
    return CreateUser()


@pytest.fixture
def f_clickhouse_client():    
    client = get_client(
        host=settings.CLICKHOUSE_HOST,
        port=settings.CLICKHOUSE_PORT,
        username=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
        database=settings.CLICKHOUSE_SCHEMA,
    )
    yield client
    client.close()


@pytest.fixture(autouse=True)
def f_clean_up(f_clickhouse_client):    
    f_clickhouse_client.command(f'TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}')
    OutboxLog.objects.all().delete()
    yield


# Test 1: Test Creating User and Storing Event in PostgreSQL Outbox
def test_user_created_stores_event_in_outbox(f_use_case: CreateUser):
    request = CreateUserRequest(
        email='test@email.com', first_name='Test', last_name='Testovich',
    )
    response = f_use_case.execute(request)
    assert response.result.email == 'test@email.com'
    assert response.error == ''
    outbox_event = OutboxLog.objects.filter(event_type='user_created').first()
    assert outbox_event is not None
    assert outbox_event.processed is False
    assert outbox_event.event_context == {
        "email": "test@email.com",
        "first_name": "Test",
        "last_name": "Testovich",
    }


# Test 2: Test Emails are Unique
def test_emails_are_unique(f_use_case: CreateUser):
    request = CreateUserRequest(
        email='test@email.com', first_name='Test', last_name='Testovich',
    )
    f_use_case.execute(request)
    response = f_use_case.execute(request)
    assert response.result is None
    assert response.error == 'User with this email already exists'


# Test 3: Test Celery Worker Reads Event from PostgreSQL and Inserts into ClickHouse
def test_event_log_entry_published(
    f_use_case: CreateUser,
    f_clickhouse_client,
):
    email = f'test_{uuid.uuid4()}@email.com'
    request = CreateUserRequest(
        email=email, first_name='Test', last_name='Testovich',
    )
    f_use_case.execute(request)    
    process_logs(batch_size=10)    
    log = f_clickhouse_client.query(
        f"SELECT * FROM {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME} WHERE event_type = 'user_created'"
    )
    assert log.result_rows[0][2] == 'Local'

# Test 4: Test Batch Processing
def test_batch_insertion_to_clickhouse(f_use_case: CreateUser, f_clickhouse_client):
    for i in range(10):
        email = f'batch_user_{i}@test.com'
        request = CreateUserRequest(email=email, first_name="Batch", last_name=f"User{i}")
        f_use_case.execute(request)    
    assert OutboxLog.objects.filter(processed=False).count() == 10    
    process_logs(batch_size=5)    
    first_batch = f_clickhouse_client.query(f"SELECT COUNT(*) FROM {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}")
    assert first_batch.result_rows[0][0] == 5    
    process_logs(batch_size=5)
    second_batch = f_clickhouse_client.query(f"SELECT COUNT(*) FROM {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}")
    assert second_batch.result_rows[0][0] == 10    
    assert OutboxLog.objects.filter(processed=False).count() == 0


# Test 5: Verify Event Context is Valid Pydantic Model
def test_event_context_is_pydantic_model(f_use_case: CreateUser, f_clickhouse_client):
    email = f'test_{uuid.uuid4()}@email.com'
    request = CreateUserRequest(email=email, first_name="Pydantic", last_name="Model")
    f_use_case.execute(request)    
    process_logs(batch_size=10)   
    log = f_clickhouse_client.query(
        f"SELECT event_context FROM {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME} WHERE event_type = 'user_created'"
    )
    event_context_json = json.loads(log.result_rows[0][0])
    event_context_dict = json.loads(event_context_json) if isinstance(event_context_json, str) else event_context_json
    user_model = UserCreated(**event_context_dict)
    assert user_model.email == email
    assert user_model.first_name == "Pydantic"
    assert user_model.last_name == "Model"

