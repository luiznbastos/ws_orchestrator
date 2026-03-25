from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from orchestrator.utils.parameters import FlowType
import boto3
from botocore.exceptions import ClientError
import logging
import os

logger = logging.getLogger(__name__)


class OrchestratorSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / '.env'),
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    run_id: str = Field(default='', description="Unique identifier for the orchestration run")
    flow_type: FlowType = Field(default=FlowType.DAILY, description="Type of flow to execute")
    tournament_name: str = Field(default="laliga", description="Name of the tournament")
    tournament_url: str = Field(default="https://www.whoscored.com/regions/206/tournaments/4", description="URL of the tournament to scrape")
    scrapping_type: str = Field(default="DATE_RANGE", description="Type of scraping strategy")
    driver_type: str = Field(default="CHROMIUM", description="Web driver type to use")
    max_keys_per_unit: int = Field(default=10, description="Maximum keys per processing unit")
    max_workers: int = Field(default=5, description="Maximum number of parallel workers")
    project_name: str = Field(default="ws-analytics", description="Project name for AWS resources")
    
    aws_region: str = Field(default="us-east-1", description="AWS region")
    prefect_home: str = Field(default="/tmp/prefect", description="Prefect home directory")

    created_ts: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when this settings instance was created (used for run consistency)"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date for data processing"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date for data processing"
    )

    def _get_ssm_parameter(self, name: str) -> Optional[str]:
        """Fetch parameter from AWS Systems Manager Parameter Store"""
        if not self._ssm_client:
            return None
        try:
            response = self._ssm_client.get_parameter(Name=name, WithDecryption=True)
            return response.get("Parameter", {}).get("Value")
        except (ClientError, self._ssm_client.exceptions.ParameterNotFound):
            logger.warning(f"Parameter {name} not found in SSM.")
            return None

    @property
    def _ssm_client(self):
        """Lazy-load SSM client"""
        if not hasattr(self, "__ssm_client"):
            try:
                self.__ssm_client = boto3.client("ssm", region_name=self.aws_region)
            except ClientError as e:
                logger.warning(f"Could not create Boto3 SSM client. Error: {e}")
                self.__ssm_client = None
        return self.__ssm_client

    @property
    def s3_bucket(self) -> Optional[str]:
        """Get S3 infra bucket name from SSM Parameter Store"""
        if not hasattr(self, "_s3_bucket"):
            ssm_path = f"/{self.project_name}/s3/infra/name"
            self._s3_bucket = self._get_ssm_parameter(ssm_path)
            logger.info(f"Loaded S3 bucket from SSM: {self._s3_bucket}")
        return self._s3_bucket

    @field_validator('created_ts', mode='before')
    @classmethod
    def always_use_now(cls, v):
        """Always use datetime.now() regardless of input or env vars"""
        return datetime.now()
    
    @field_validator('flow_type', mode='before')
    @classmethod
    def parse_flow_type(cls, v):
        """Parse string flow type to enum"""
        if isinstance(v, str):
            return FlowType[v.upper()]
        return v

settings = OrchestratorSettings()
