from datetime import timedelta
import os
from prefect import task, get_run_logger
from orchestrator.utils.aws_batch import submit_batch_job

TRANSFORMER_TIMEOUT = 3600

@task(
    cache_expiration=None,
    retry_delay_seconds=60,
    retries=5,
)
async def submit_transformation_job(
    run_id: str,
    start_date: str,
    end_date: str,
    scrape_run_id: str,
    max_keys_per_unit: int,
    max_workers: int,
    run_type: str = None,
):
    """
    Task to submit transformation job to AWS Batch.
    This replicates the ws_transform_task from the Airflow DAG.
    """
    
    logger = get_run_logger()
    logger.info(f"Submitting transformation job for run_id: {run_id}")
    
    # Get RUN_TYPE from environment if not provided, default to DATE_RANGE
    if run_type is None:
        run_type = os.environ.get("RUN_TYPE", "DATE_RANGE")
    
    timeout = TRANSFORMER_TIMEOUT
    job_name = f"ws-transform-{run_id[:8]}"
    job_definition = 'ws-analytics-preprocessing'
    job_queue = 'ws-analytics-job-queue'
    
    env = [
        {"name": "RUN_ID", "value": run_id},
        {"name": "START_DATE", "value": start_date},
        {"name": "END_DATE", "value": end_date},
        {"name": "RUN_TYPE", "value": run_type},
        {"name": "SCRAPE_RUN_ID", "value": scrape_run_id},
        {"name": "MAX_KEYS_PER_UNIT", "value": str(max_keys_per_unit)},
        {"name": "MAX_WORKERS", "value": str(max_workers)},
    ]
    env = [item for item in env if item["value"] is not None]

    batch_kwargs = {
        "timeout": {
            "attemptDurationSeconds": timeout,
        },
        "containerOverrides": {
            "environment": env,
        }
    }
    
    logger.info(f"Submitting batch job with definition: {job_definition}")
    job_id = await submit_batch_job(
        job_name=job_name,
        job_definition=job_definition,
        job_queue=job_queue,
        batch_kwargs=batch_kwargs,
    )
    
    logger.info(f"Transformation job completed with job_id: {job_id}")
    return job_id


