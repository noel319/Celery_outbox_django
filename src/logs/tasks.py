import structlog
from celery import shared_task
from logs.services import process_logs
from sentry_sdk import start_transaction

logger = structlog.get_logger(__name__)

@shared_task(bind=True)
def process_outbox_task(self, *args, **kwargs):
    with start_transaction(op="celery_task", name="process_outbox_task") as transaction:
        logger.info("Starting outbox processing", 
                    task_id=self.request.id, 
                    transaction_id=transaction.trace_id
                    )
        try:
            processed_count = process_logs()
            logger.info(
                "Completed outbox processing",
                task_id=self.request.id,
                transaction_id=transaction.trace_id,
                processed_count=processed_count,
            )
        except Exception as e:
            logger.error("Failed to process outbox logs", 
                        task_id=self.request.id, 
                        transaction_id=transaction.trace_id, 
                        error=str(e)
                        )
            raise
