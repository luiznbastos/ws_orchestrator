# Reference central infrastructure via SSM parameters
data "aws_ssm_parameter" "ecr_url" {
  name = "/${var.project_name}/ecr/${var.job_name}/url"
}

data "aws_ssm_parameter" "job_queue_arn" {
  name = "/${var.project_name}/batch/job-queue-arn"
}

# Reference all other job ARNs for orchestration
data "aws_ssm_parameter" "scrapping_job_arn" {
  name = "/${var.project_name}/batch/jobs/scrapping/arn"
}

# Note: preprocessing and dbt job ARNs are optional and may not exist yet
# data "aws_ssm_parameter" "preprocessing_job_arn" {
#   name = "/${var.project_name}/batch/jobs/preprocessing/arn"
# }

# data "aws_ssm_parameter" "dbt_job_arn" {
#   name = "/${var.project_name}/batch/jobs/dbt/arn"
# }

# Reference S3 buckets for IAM policy construction
data "aws_ssm_parameter" "infra_bucket" {
  name = "/${var.project_name}/s3/infra/name"
}

data "aws_ssm_parameter" "analytics_bucket" {
  name = "/${var.project_name}/s3/analytics/name"
}

# Fetch shared policies from central repo
data "aws_iam_policy" "ssm_policy" {
  name = "${var.project_name}-ssm-policy"
}

data "aws_iam_policy" "cloudwatch_policy" {
  name = "${var.project_name}-cloudwatch-policy"
}



