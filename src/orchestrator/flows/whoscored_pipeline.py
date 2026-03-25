from prefect import flow, get_run_logger
from prefect.futures import PrefectFuture
from prefect.filesystems import S3
from orchestrator.utils.cache import on_completed, get_s3_storage_path
from orchestrator.tasks.scraper import submit_scraping_job
from orchestrator.tasks.transformer import submit_transformation_job


@flow(
    name="WhoScored Data Pipeline",
    on_completion=[on_completed],
    on_failure=[on_completed],
    on_cancellation=[on_completed],
    on_crashed=[on_completed],
    persist_result=True,
    result_storage=S3(bucket_path=get_s3_storage_path())
)
async def whoscored_pipeline_flow(
    run_id: str,
    start_date: str,
    end_date: str,
    tournament_url: str,
    tournament_name: str,
    scrapping_type: str,
    driver_type: str,
    max_keys_per_unit: int,
    max_workers: int,
    force_refresh_seasons: bool = False,
    force_refresh_matches: bool = False,
    force_refresh_events: bool = False,
):
    """
    Main pipeline flow that orchestrates the WhoScored data processing.
    This replicates the Airflow DAG sequence:
    1. Scraping task (batch_scrapper)
    2. Transformation task (ws_batch_transform)
    """
    logger = get_run_logger()
    logger.info(f"Starting WhoScored pipeline for run {run_id}")
    
    try:
        logger.info("Step 1: Submitting scraping job")
        scrape_future: PrefectFuture = await submit_scraping_job.submit(
            run_id=run_id,
            start_date=start_date,
            end_date=end_date,
            tournament_url=tournament_url,
            tournament_name=tournament_name,
            scrapping_type=scrapping_type,
            driver_type=driver_type,
            force_refresh_seasons=force_refresh_seasons,
            force_refresh_matches=force_refresh_matches,
            force_refresh_events=force_refresh_events,
        )
        scrape_job_id = await scrape_future.result()
        logger.info(f"Scraping job completed with job_id: {scrape_job_id}")
        logger.info(f"Scrape job ID type: {type(scrape_job_id)}, value: {repr(scrape_job_id)}")

        logger.info("Step 2: Submitting transformation job")
        transform_future: PrefectFuture = await submit_transformation_job.submit(
            run_id=run_id,
            start_date=start_date,
            end_date=end_date,
            scrape_run_id=run_id,
            max_keys_per_unit=max_keys_per_unit,
            max_workers=max_workers,
            wait_for=[scrape_future],
        )
        transform_job_id = await transform_future.result()
        logger.info(f"Transformation job completed with job_id: {transform_job_id}")
    except Exception as e:
        logger.error(f"Flow failed with error: {e}")
        raise
    
    logger.info(f"WhoScored pipeline completed successfully for run {run_id}")
    return {"scrape_job_id": scrape_job_id, "transform_job_id": transform_job_id}
