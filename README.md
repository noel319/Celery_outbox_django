 # Event Logging System with Outbox Pattern 
 
 ## Summary
This project is a robust event logging system designed to handle high-throughput event data, store events in PostgreSQL using the outbox pattern, and process them with Celery to batch insert into ClickHouse. This setup ensures data reliability, reduces database load by batching inserts, and provides transactionality, improving resilience against worker failures.

### Key components:

- **Django** as the primary web framework.
- **PostgreSQL** for outbox storage, ensuring transactionality.
- **Celery** for asynchronous and periodic task processing.
- **ClickHouse** for fast event log storage and retrieval.
- **Redis** as a message broker for Celery.
- **Flower** for real-time monitoring of Celery tasks.
- **Sentry** for error tracking and transaction tracing.

## Installation
### Prerequisites
Ensure you have Docker and Docker Compose installed.

### Steps
Clone the repository:

bash
Copy code
git clone <repository-url>
cd <repository-folder>
### Set up environment variables:

Copy the example environment variables:
bash
Copy code
cp src/core/.env.example src/core/.env
Modify src/core/.env with the appropriate values for your database and other configurations.
### Build and Start the Docker Containers:

bash
Copy code
docker-compose up --build
Run Migrations: After all services are up, apply the database migrations:

bash
Copy code
docker-compose exec web python src/manage.py migrate
Access the Application and Flower:

Django application: http://localhost:8000
Flower monitoring: http://localhost:5555
Run Tests: Execute the test suite to ensure everything is working correctly:

bash
Copy code
docker-compose exec web pytest src/tests/
## Project Logic
The project follows the Outbox Pattern to ensure reliable event logging. Here’s how it works:

### Event Generation:

When an event occurs, it is stored in a PostgreSQL outbox table within a transaction, ensuring that even if the application crashes, the event is recorded in the database.
Batch Processing with Celery:

A periodic Celery task retrieves unprocessed events from the outbox and attempts to insert them in bulk into ClickHouse.
If the insert to ClickHouse succeeds, the events are marked as processed in the outbox.
If it fails, the task retries using Celery’s retry mechanism, and errors are logged in Sentry.
Monitoring with Flower and Sentry:

Flower provides real-time monitoring of Celery tasks, showing active, scheduled, and completed tasks.
Sentry captures any errors and traces transactions, offering insights into retry attempts and performance.
System Architecture Diagram
plaintext
Copy code
                    +---------------+
                    |  Event Source |
                    +-------+-------+
                            |
                            v
                     +-------------+
                     | Outbox Table |
                     +-------------+
                            |
                            v
                 +----------+-----------+
                 | Celery Worker (Batch |
                 | Processing)          |
                 +----------+-----------+
                            |
                            v
                      +------------+
                      | ClickHouse  |
                      +------------+
This flow ensures that events are reliably stored in PostgreSQL before being processed by Celery and sent to ClickHouse in batches.

## Improved Solution
Through research on the outbox pattern and Celery usage, here are some recommended enhancements for greater reliability and efficiency.

### 1. Optimized Outbox Processing with Bulk Insertion and Deduplication
A common challenge with high-throughput systems is handling large volumes of events without overloading the database. To improve performance:

Batch Insert with Django's bulk_create: Use Django’s bulk_create for high-throughput event logging to PostgreSQL to reduce transaction overhead.
Deduplication Mechanism: Implement a deduplication check on the outbox table by defining unique constraints for events, which ensures each event is processed only once, even after retries.
### 2. Enhanced Celery Configuration for Scalability and Reliability
To make Celery more resilient and scalable:

Task Rate Limiting: Set Celery rate limits to control task consumption based on processing capacity, preventing overload during traffic spikes.
Retry Policies: Configure an exponential backoff retry strategy for Celery to handle intermittent failures gracefully, which is particularly helpful for network-related errors.
Example retry configuration:

python
Copy code
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, max_retries=10)
def push_to_clickhouse(self):
    ...
This configuration:

Uses retry_backoff=True for exponential backoff.
Limits retries to every 10 minutes (retry_backoff_max=600) with a maximum of 10 retries.
### 3. Partitioned ClickHouse Table for Optimized Event Storage
Partitioning can help ClickHouse handle large datasets by reducing the load on individual inserts and reads:

Monthly Partitioning by Event Date: Configure ClickHouse tables to partition data by month using the event date, which improves query performance and makes batch inserts more efficient.
In init.sql for ClickHouse:

sql
Copy code
CREATE TABLE IF NOT EXISTS event_log
(
    event_type String,
    event_date_time DateTime64(6),
    environment String,
    event_context String,
    metadata_version UInt64
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date_time)
ORDER BY (event_date_time, event_type)
SETTINGS index_granularity = 8192;
### 4. Monitoring and Alerting Enhancements
Beyond Sentry for error tracking, you could implement:

Prometheus and Grafana: For detailed metrics on task processing, including Celery task counts, worker load, and latency.
ClickHouse Monitoring: Integrate ClickHouse-specific metrics to monitor insert speeds, storage utilization, and query times.
Conclusion
This project demonstrates a reliable, high-throughput event logging system using the outbox pattern and Celery for batch processing. The suggested improvements enhance scalability, performance, and reliability, ensuring the system is equipped to handle high event volumes and operational challenges.

