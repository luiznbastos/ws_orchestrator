import boto3
from asyncio import sleep
from typing import Dict, Any, Optional
from prefect import get_run_logger
from prefect_aws.batch import batch_submit
from prefect_aws.credentials import AwsCredentials
from orchestrator.settings import settings

async def submit_batch_job(
    job_name: str,
    job_definition: str,
    job_queue: str,
    batch_kwargs: Optional[Dict[str, Any]],
    wait_for_completion: bool = True,
    **kwargs: Optional[Dict[str, Any]],
) -> str:
    """
    Submit a batch job and wait for it to complete.
    """
    
    logger = get_run_logger()
    aws_credentials = get_aws_credentials()
    
    job_id = await batch_submit.fn(
        job_name=job_name,
        job_definition=job_definition,
        job_queue=job_queue,
        aws_credentials=aws_credentials,
        **batch_kwargs,
    )
    
    logger.info(f"Batch job {job_name} submitted with id {job_id}")
    
    if wait_for_completion:
        await wait_for_batch_job(job_id)
        
    return job_id


async def wait_for_batch_job(job_id: str) -> None:
    """
    Wait for a batch job to complete.
    """
    
    logger = get_run_logger()
    session = boto3.Session(region_name=settings.aws_region)
    client = session.client('batch')
    
    while True:
        response = client.describe_jobs(jobs=[job_id])
        if response['jobs'][0]['status'] in ['SUCCEEDED', 'FAILED']:
            break
        
        await sleep(15)
        
    if response['jobs'][0]['status'] == 'SUCCEEDED':
        logger.info(f"Batch job {job_id} completed successfully")
    else:
        logger.error(f"Batch job {job_id} failed")
        raise Exception(f"Batch job {job_id} failed")
        
def get_aws_credentials() -> AwsCredentials:
    """
    Get the AWS credentials from the environment variables.
    """
    
    logger = get_run_logger()
    session = boto3.Session(region_name=settings.aws_region)

    aws_credentials = session.get_credentials().get_frozen_credentials()

    if not aws_credentials:
        raise ValueError("AWS credentials not found")
    
    aws_credentials = AwsCredentials(
        aws_access_key_id=aws_credentials.access_key,
        aws_secret_access_key=aws_credentials.secret_key,
        aws_session_token=aws_credentials.token,
        region_name=settings.aws_region
    )    
    logger.info("AWS credentials loaded successfully")
    return aws_credentials


