import os, uuid, s3fs
from datetime import datetime
from prefect import get_run_logger
from orchestrator.utils.parameters import FlowType, RunStage, RunStatus
from orchestrator.utils.logger import get_logger
from orchestrator.settings import settings

def get_s3_storage_path():
    return f"s3://{settings.s3_bucket}/prefect/whoscored/{settings.created_ts.strftime('%Y-%m-%d')}"

def get_s3_state_path():
    return f"s3://{settings.s3_bucket}/prefect/states/{settings.created_ts.strftime('%Y-%m-%d')}"

def local_prefect_path():
    return settings.prefect_home

def load_flow_state(run_id: str):
    logger = get_run_logger()
    logger.info(f"Loading flow state from previous run: {run_id}")
    state_path = get_s3_state_path()
    local_path = local_prefect_path()

    s3_file = s3fs.S3FileSystem(
        key=os.environ.get('AWS_ACCESS_KEY_ID'),
        secret=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=settings.aws_region
    )
    if s3_file.exists(state_path):
        s3_file.get(state_path, local_path)
        logger.info(f"Loaded previous state from {state_path}")
        return True
    
    logger.info(f"Previous state not found at {state_path}")
    return False
    
def save_flow_state(run_id: str):
    logger = get_run_logger()
    state_path = get_s3_state_path()
    local_path = local_prefect_path()
    logger.info(f"Saving flow state to {state_path}")
    
    s3_file = s3fs.S3FileSystem(
        key=os.environ.get('AWS_ACCESS_KEY_ID'),
        secret=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=settings.aws_region
    )
    
    s3_file.put(local_path, state_path, recursive=True)
    logger.info(f"Saved flow state to {state_path}")

def on_completed(flow, flow_run, state):
    logger = get_logger(__name__)
    logger.info(f"Flow {flow_run.parameters['run_id']} completed with state {state.name}")
    
    try:
        save_flow_state(flow_run.parameters['run_id'])
    except Exception as e:
        logger.error(f"Failed to save flow state: {e}")

def generate_run_id():
    """
    Generate a new run_id.
    """
    # logger = get_run_logger()
    run_id = str(uuid.uuid4())
    # logger.info(f"Generated new run_id: {run_id}")
    return run_id

def get_run_id_and_state():
    """
    Generate a new run_id for the flow.
    """
    # logger = get_run_logger()
    run_id = generate_run_id()
    return run_id
