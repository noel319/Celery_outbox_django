import structlog
from logs.models import OutboxLog
from core.event_log_client import EventLogClient
from sentry_sdk import start_transaction, capture_exception
import json

logger = structlog.get_logger(__name__)

def process_logs(batch_size=100) -> int:    
    with start_transaction(op="log_processing", name="process_logs") as transaction:
        logs = OutboxLog.objects.filter(processed=False)[:batch_size]
        if not logs:
            logger.info("No logs to process", transaction_id=transaction.trace_id)
            return 0
        
        logger.info("Processing logs",
                    transaction_id=transaction.trace_id,
                    log_count=len(logs)
                    )
        
        data_to_insert = []
        for log in logs:
            try:               
                data_to_insert.append({
                    "event_type": log.event_type,
                    "event_date_time": log.event_date_time,
                    "environment": log.environment,
                    "event_context": json.dumps(log.event_context),
                    "metadata_version": log.metadata_version,
                })
            except Exception as e:
                logger.error("Error parsing event context", event_id=log.id, error=str(e))
                capture_exception(e)
                continue
                
        with EventLogClient.init() as client:
            try:
                client.insert(data=data_to_insert)
                log_ids = [log.id for log in logs] 
                OutboxLog.objects.filter(id__in=log_ids).update(processed=True)                
                logger.info(
                    "Successfully processed logs", 
                    transaction_id=transaction.trace_id,                       
                    processed_count=len(data_to_insert),
                )
                return len(data_to_insert)                
            except Exception as e:
                capture_exception(e)
                logger.error("Error processing logs", 
                            transaction_id=transaction.trace_id, 
                            error=str(e)
                            )
                raise
