# Backend test task

Expected completion time: 3-5 hours

You will be given a short description of a problem along with several basic restrictions and requirements.

As we expect the candidate to be able to work (or quickly adapt to) our tech stack,
you will also be given a list of recommended technologies.


As a result create repository from this repo template and submit the link to your repository via [this Typeform](https://hiretechfast.typeform.com/to/QZ55qiDi)


The repository must contain:

- a short manual on how to set up the project after the changes
- code with tests, logs and tracing (you can use sentry transactions)
- documentation that describes your technical solution and design (you can optionally provide a diagram)

## Stack

- Python
- Django
- pytest (pytest-django preferred for fixtures)
- Docker & docker-compose
- PostgreSQL
- Celery & Celery beat
- ClickHouse (already installed in docker)

## The Problem

Our application sends event logs that are later used for business analysis, incident investigations and security audits.

To store these logs we use a column-based database Clickhouse and the so-called One Big Table (further referred to as OBT) - a wide table that
contains the following columns (the columns may be extended in the future):

```
event_type: String
event_date_time: DateTime
environment: String
event_context: String // JSON field with unstructured payload
metadata_version: UInt64 // for versioning purposes
```

The application pushes logs synchronously directly to CH, see an example in the `CreateUser` use case.

This approach has caused several problems, such as:

- due to the lack of transactionality logs are missed in case of a web-worker failure before the business-logic step is executed
- Clickhouse network write errors cause poor UX
- Clickhouse struggles with large numbers of small inserts (see https://clickhouse.com/blog/common-getting-started-issues-with-clickhouse#many-small-inserts)

We need to implement a new write mechanism that will eliminate those problems and provide a convenient interface for publishing logs

**Restrictions and requirements:**

- for the sake of simplicity we don't want to use Kafka for event streaming.
- we don't want to use Clickhouse-specific features such as RabbitMQ/Kafka engine for publishing logs since there is a chance that Clickhouse will be replaced with another database down the line
- we don't want to use external file storage, like AWS S3
- the `event_context` field contains unstructured JSON payload up to N MBytes so it may not be a good idea to push it directly to a queue
- `Transactional outbox pattern` might be useful for this problem
- we would like to see a simple and efficient solution that uses a well-known tech stack for ease of maintenance, monitoring and debugging
