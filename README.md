# WhoScored Orchestrator

## Project Overview (Shared)
- Business objective: deliver actionable soccer performance insights from historical and near‑real‑time data, inspired by Soccermatics methods (https://soccermatics.readthedocs.io/en/latest/index.html).
- Pipeline (end‑to‑end):
  - ws_scrapping: acquire raw match/event data from web sources/APIs
  - ws_preprocessing: validate, normalize, and load to staging (S3→Parquet→Redshift when applicable)
  - ws_dbt: transform into bronze/silver/gold models for analytics (team/player/match)
  - ws_orchestrator: schedule and monitor flows (S3 state when applicable)
  - ws_streamlit: visualize KPIs and match insights
  - ws_infrastructure: IaC for compute, storage, security, CI/CD
- Data stores: AWS S3 and Redshift are primary; not all steps use both.
- Future (planned next year): add an xG/xT training job; extend the pipeline/dbt (Python models or external tasks) to load trained parameters, infer and persist xG/xT per event, and compute aggregates, using dbt tags to separate standard vs inference runs.

## Producer–Consumer Pattern
- Consumer of shared infrastructure produced by `ws_infrastructure`.
- Consumes from SSM:
  - Batch job queue ARN: `/${project}/batch/job-queue-arn`
  - Scrapping job ARN: `/${project}/batch/jobs/scrapping/arn` (and others when defined)
- Produces: Orchestration job definition, S3 state objects, run metadata/logs.

This orchestrator service manages the WhoScored data pipeline using Prefect and AWS Batch. It replaces the previous Airflow-based orchestration with a lightweight, cloud-native solution.

## Overview

The orchestrator runs two sequential tasks:
1. **Scraping Job**: Scrapes data from WhoScored.com using the `batch-scraper` job definition
2. **Transformation Job**: Processes and transforms the scraped data using the `batch-transformer` job definition

## Orchestration & Pipeline Context
- Cloud execution: this service triggers the pipeline tasks on AWS Batch.
- Sequence: triggers `ws_scrapping` → waits → triggers `ws_preprocessing` → (later) triggers `ws_dbt`.
- Previous step: none (entrypoint for scheduled runs).
- Next step: downstream tasks consume outputs to populate models and dashboards.

## Architecture

- **Orchestration**: Prefect for workflow management
- **Configuration**: Pydantic Settings for type-safe configuration management
- **Execution**: AWS Batch for job execution
- **Storage**: S3 for state persistence and results
- **Job Definitions**: Docker-based AWS Batch job definitions

## Features

- ✅ Sequential task execution (scraping → transformation)
- ✅ AWS Batch job submission and monitoring
- ✅ S3 state persistence for resume capability
- ✅ Automatic retry with exponential backoff
- ✅ Task result caching
- ✅ Flow completion hooks
- ✅ Comprehensive logging

## Configuration

The orchestrator uses **Pydantic Settings** for type-safe configuration management. All settings can be provided via environment variables or a `.env` file.

### Required
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `S3_BUCKET`: S3 bucket for state and results storage

### Optional (with defaults)
- `RUN_ID`: Unique identifier for the pipeline run (auto-generated if not provided)
- `FLOW_TYPE`: Type of flow to run (DAILY, CUSTOM, BACKFILL) - default: DAILY
- `START_DATE`: Start date for data processing (format: YYYY-MM-DD) - default: 2 years ago
- `END_DATE`: End date for data processing (format: YYYY-MM-DD) - default: today
- `TOURNAMENT_URL`: URL of the tournament to scrape - default: LaLiga URL
- `TOURNAMENT_NAME`: Name of the tournament (e.g., laliga) - default: laliga
- `SCRAPPING_TYPE`: Type of scraping (DATE_RANGE, DAILY) - default: DATE_RANGE
- `DRIVER_TYPE`: Browser driver type (CHROMIUM, FIREFOX) - default: CHROMIUM
- `MAX_KEYS_PER_UNIT`: Maximum keys per processing unit - default: 10
- `MAX_WORKERS`: Maximum number of parallel workers - default: 5
- `AWS_REGION`: AWS region - default: us-east-1
- `PREFECT_HOME`: Prefect home directory - default: /tmp/prefect

All settings are validated at startup and provide helpful error messages if misconfigured.

## AWS Batch Job Definitions Required

You need to create the following AWS Batch job definitions:

1. **batch-scraper**: Points to the batch_scrapper Docker image
2. **batch-transformer**: Points to the ws_batch_transform Docker image

## Usage

### Local Development

#### Quick Start

1. **Set up environment variables**:
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env with your AWS credentials
   # Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the orchestrator**:
   ```bash
   # Set Python path and run
   export PYTHONPATH=/path/to/ws_orchestrator/src
   python src/runner.py
   ```

#### Environment Variables

The orchestrator uses the following environment variables (see `.env.example`):

**Required:**
- `AWS_ACCESS_KEY_ID`: Your AWS access key (used by boto3 and s3fs)
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key (used by boto3 and s3fs)
- `S3_BUCKET`: S3 bucket for state storage (e.g., `terraform-ws-analytics-infra`)

**Optional (with defaults):**
- `AWS_REGION`: AWS region (default: `us-east-1`)
- `TOURNAMENT_URL`: Tournament URL (default: LaLiga URL)
- `TOURNAMENT_NAME`: Tournament name (default: `laliga`)
- `FLOW_TYPE`: Flow type (default: `DAILY`)
- `START_DATE`: Start date (default: 2 years ago, auto-calculated)
- `END_DATE`: End date (default: today, auto-calculated)
- `SCRAPPING_TYPE`: Scraping strategy (default: `DATE_RANGE`)
- `DRIVER_TYPE`: Web driver type (default: `CHROMIUM`)
- `MAX_KEYS_PER_UNIT`: Max keys per processing unit (default: `10`)
- `MAX_WORKERS`: Max parallel workers (default: `5`)
- `PREFECT_HOME`: Prefect home directory (default: `/tmp/prefect`)

#### Monitoring Local Runs

When running locally, you can monitor the AWS Batch jobs:

1. **AWS Batch Console**: https://console.aws.amazon.com/batch/home?region=us-east-1#/jobs
2. **Look for jobs in queue**: `ws-analytics-job-queue`
3. **Job naming pattern**: `ws-scraping-{run_id[:8]}`
4. **S3 State**: Check your S3 bucket for Prefect state and results

#### Expected Output

```
2024-01-15 10:30:00 - orchestrator.pipeline - INFO - Starting WhoScored orchestration pipeline
2024-01-15 10:30:00 - orchestrator.pipeline - INFO - Using run_id abc12345-... to run the pipeline
2024-01-15 10:30:01 - orchestrator.tasks.scraper - INFO - Submitting scraping job for run_id: abc12345-...
2024-01-15 10:30:02 - orchestrator.utils.aws_batch - INFO - Batch job ws-scraping-abc12345 submitted with id job-12345
2024-01-15 10:30:02 - orchestrator.utils.aws_batch - INFO - Waiting for batch job job-12345 to complete...
```

### Docker

```bash
# Build the image
make build

# Push to ECR
make push

# Test locally
make test
```

### AWS Batch Deployment

The orchestrator runs as an AWS Batch job definition. Follow these steps to deploy:

#### Prerequisites

1. **Infrastructure deployed**: Ensure the main infrastructure (`ws_infrastructure`) is deployed
2. **ECR image pushed**: Build and push the orchestrator Docker image to ECR
3. **Job definitions exist**: Ensure `batch-scraper` and `batch-transformer` job definitions exist

#### Deploy with Terraform

```bash
cd terraform/

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Deploy the orchestrator job definition
terraform apply
```

This creates:
- **Job Definition**: `ws-analytics-orchestrator` 
- **IAM Role**: With Batch submit/describe and S3 access permissions
- **SSM Parameters**: For referencing other job definitions

#### Triggering the Job

**Manual Trigger**:
```bash
aws batch submit-job \
  --job-name "orchestration-$(date +%Y%m%d-%H%M%S)" \
  --job-queue "ws-analytics-job-queue" \
  --job-definition "ws-analytics-orchestrator" \
  --parameters '{"RUN_ID":"manual-test-123","TOURNAMENT_NAME":"laliga"}'
```

**EventBridge Schedule** (optional):
```bash
# Create a daily schedule at 2 AM UTC
aws events put-rule \
  --name "ws-orchestration-daily" \
  --schedule-expression "cron(0 2 * * ? *)" \
  --description "Daily WhoScored data pipeline"

# Add the Batch job as a target
aws events put-targets \
  --rule "ws-orchestration-daily" \
  --targets "Id"="1","Arn"="arn:aws:batch:us-east-1:ACCOUNT:job-queue/ws-analytics-job-queue","RoleArn"="arn:aws:iam::ACCOUNT:role/EventBridge-Batch-Role","BatchParameters"="{\"JobDefinition\":\"ws-analytics-orchestrator\",\"JobName\":\"daily-orchestration\"}"
```

#### Monitoring Deployed Jobs

1. **AWS Batch Console**: Monitor job status and logs
2. **CloudWatch Logs**: `/aws/batch/ws-analytics` log group
3. **S3 Bucket**: Check for state persistence and results

## Project Structure

```
ws_orchestrator/
├── src/
│   ├── orchestrator/
│   │   ├── flows/
│   │   │   └── whoscored_pipeline.py    # Main pipeline flow
│   │   ├── tasks/
│   │   │   ├── scraper.py                # Scraping task
│   │   │   └── transformer.py            # Transformation task
│   │   ├── utils/
│   │   │   ├── aws_batch.py              # AWS Batch utilities
│   │   │   ├── cache.py                  # S3 caching and state management
│   │   │   ├── logger.py                 # Logging configuration
│   │   │   └── parameters.py             # Enums and parameters
│   │   ├── settings.py                   # Pydantic settings configuration
│   │   └── pipeline.py                   # Pipeline entry point
│   └── runner.py                         # Main runner script
├── Dockerfile
├── Makefile
├── requirements.txt
└── README.md
```

## Comparison with Previous Airflow Setup

| Feature | Airflow | Prefect + AWS Batch |
|---------|---------|---------------------|
| Orchestration | Airflow DAG | Prefect Flow |
| Task Execution | Docker on local machine | AWS Batch jobs |
| State Storage | Airflow DB | S3 |
| Retry Logic | Built-in | Built-in with better control |
| Monitoring | Airflow UI | Prefect UI + CloudWatch |
| Infrastructure | Heavy (multiple services) | Lightweight (single container) |
| Scalability | Limited by local resources | Scales with AWS Batch |

## Migration Notes

The pipeline preserves the same logical sequence as the Airflow DAG:
- `ws_data_scrapping` → `submit_scraping_job`
- `ws_data_transform` → `submit_transformation_job`

All environment variables from the original Airflow tasks are preserved and passed to the AWS Batch jobs.


