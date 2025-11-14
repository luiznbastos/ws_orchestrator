from orchestrator.utils.logger import get_logger
from orchestrator.utils.parameters import FlowType
from orchestrator.utils.cache import get_run_id_and_state
from orchestrator.flows.whoscored_pipeline import whoscored_pipeline_flow
from orchestrator.settings import settings
import asyncio

logger = get_logger(__name__)

def start_pipeline():
    if not settings.run_id or settings.run_id == 'auto-generated-if-not-provided':
        settings.run_id = get_run_id_and_state()
    logger.info(f"Using run_id {settings.run_id} to run the pipeline ...")
    
    if not settings.start_date or not settings.end_date:
        raise ValueError("START_DATE and END_DATE must be set in .env file")
    
    if settings.flow_type == FlowType.DAILY or settings.flow_type == FlowType.CUSTOM:
        asyncio.run(whoscored_pipeline_flow(
            run_id=settings.run_id,
            start_date=settings.start_date,
            end_date=settings.end_date,
            tournament_url=settings.tournament_url,
            tournament_name=settings.tournament_name,
            scrapping_type=settings.scrapping_type,
            driver_type=settings.driver_type,
            max_keys_per_unit=settings.max_keys_per_unit,
            max_workers=settings.max_workers,
        ))
    else:
        raise ValueError(f"Invalid flow type: {settings.flow_type}")
