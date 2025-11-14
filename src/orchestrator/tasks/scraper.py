from datetime import timedelta
from prefect import task, get_run_logger
from orchestrator.utils.aws_batch import submit_batch_job

SCRAPER_TIMEOUT = 7200

@task(
    cache_expiration=None,
    retry_delay_seconds=60,
    retries=5,
)
async def submit_scraping_job(
    run_id: str,
    start_date: str,
    end_date: str,
    tournament_url: str,
    tournament_name: str,
    scrapping_type: str,
    driver_type: str,
):
    """
    Task to submit scraping job to AWS Batch.
    This replicates the ws_scrapping_task from the Airflow DAG.
    """
    
    logger = get_run_logger()
    logger.info(f"Submitting scraping job for run_id: {run_id}")
    
    timeout = SCRAPER_TIMEOUT
    job_name = f"ws-scraping-{run_id[:8]}"
    job_definition = 'ws-analytics-scrapping'
    job_queue = 'ws-analytics-job-queue'
    
    env = [
        {"name": "RUN_ID", "value": run_id},
        {"name": "START_DATE", "value": start_date},
        {"name": "END_DATE", "value": end_date},
        {"name": "TOURNAMENT_URL", "value": tournament_url},
        {"name": "TOURNAMENT_NAME", "value": tournament_name},
        {"name": "SCRAPPING_TYPE", "value": scrapping_type},
        {"name": "DRIVER_TYPE", "value": driver_type},
        {"name": "SCRAPPING_DOMAIN", "value": "WHO_SCORED"},
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
    
    logger.info(f"Scraping job completed with job_id: {job_id}")
    return job_id
