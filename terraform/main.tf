# Provider configuration
provider "aws" {
  region = "eu-west-2"
}

# ECR repository to store Lambda container images
resource "aws_ecr_repository" "lambda_repo" {
  name                 = "c21-boxen-botanical-pipeline-1"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "plant-load-lambda"
    Environment = "production"
  }
}

# ECR repository for archive pipeline
resource "aws_ecr_repository" "archive_lambda_repo" {
  name                 = "c21-boxen-archive-pipeline"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "archive-pipeline"
    Environment = "production"
  }
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "c21-boxen-plant-load-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda function
resource "aws_lambda_function" "plant_load" {
  function_name = "c21-boxen-plant-load-pipeline"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda_repo.repository_url}:latest"
  timeout       = 300
  memory_size   = 512

  environment {
    variables = {
      DB_HOST     = var.db_host
      DB_PORT     = var.db_port
      DB_USER     = var.db_user
      DB_PASSWORD = var.db_password
      DB_NAME     = var.db_name
      DB_SCHEMA   = var.db_schema
    }
  }
}

# EventBridge Scheduler to trigger Lambda every minute
resource "aws_scheduler_schedule" "plant_load_schedule" {
  name       = "c21-boxen-plant-load-schedule"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(1 minute)"

  target {
    arn      = aws_lambda_function.plant_load.arn
    role_arn = aws_iam_role.scheduler_role.arn
  }
}

# IAM role for EventBridge Scheduler
resource "aws_iam_role" "scheduler_role" {
  name = "c21-boxen-eventbridge-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for Scheduler to invoke Lambda
resource "aws_iam_role_policy" "scheduler_lambda_policy" {
  name = "c21-boxen-scheduler-lambda-policy"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.plant_load.arn
      }
    ]
  })
}

# Outputs
output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.lambda_repo.repository_url
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.plant_load.function_name
}

output "archive_ecr_repository_url" {
  description = "Archive pipeline ECR repository URL"
  value       = aws_ecr_repository.archive_lambda_repo.repository_url
}

output "archive_lambda_function_name" {
  description = "Archive Lambda function name"
  value       = aws_lambda_function.archive_pipeline.function_name
}

# IAM role for Archive Lambda
resource "aws_iam_role" "archive_lambda_role" {
  name = "c21-boxen-archive-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic Lambda execution policy to archive Lambda
resource "aws_iam_role_policy_attachment" "archive_lambda_basic" {
  role       = aws_iam_role.archive_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM policy for Archive Lambda to write to S3
resource "aws_iam_role_policy" "archive_lambda_s3_policy" {
  name = "c21-boxen-archive-lambda-s3-policy"
  role = aws_iam_role.archive_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = "${aws_s3_bucket.plant_archive.arn}/*"
      }
    ]
  })
}

# Archive Lambda function
resource "aws_lambda_function" "archive_pipeline" {
  function_name = "c21-boxen-archive-pipeline"
  role          = aws_iam_role.archive_lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.archive_lambda_repo.repository_url}:latest"
  timeout       = 300
  memory_size   = 512

  environment {
    variables = {
      DB_HOST        = var.db_host
      DB_PORT        = var.db_port
      DB_USER        = var.db_user
      DB_PASSWORD    = var.db_password
      DB_NAME        = var.db_name
      DB_SCHEMA      = var.db_schema
      S3_BUCKET_NAME = aws_s3_bucket.plant_archive.id
    }
  }
}

# EventBridge Scheduler for Archive Lambda (runs at 11:59 PM UK time)
resource "aws_scheduler_schedule" "archive_schedule" {
  name       = "c21-boxen-archive-schedule"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(59 23 * * ? *)"

  target {
    arn      = aws_lambda_function.archive_pipeline.arn
    role_arn = aws_iam_role.archive_scheduler_role.arn
  }
}

# IAM role for Archive EventBridge Scheduler
resource "aws_iam_role" "archive_scheduler_role" {
  name = "c21-boxen-archive-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for Archive Scheduler to invoke Lambda
resource "aws_iam_role_policy" "archive_scheduler_lambda_policy" {
  name = "c21-boxen-archive-scheduler-lambda-policy"
  role = aws_iam_role.archive_scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.archive_pipeline.arn
      }
    ]
  })
}

# S3 bucket for daily plant summaries
resource "aws_s3_bucket" "plant_archive" {
  bucket = "c21-boxen-botanical-archive"

  tags = {
    Name        = "c21-boxen-botanical-archive"
    Environment = "production"
  }
}

output "s3_bucket_name" {
  description = "S3 bucket name for plant summaries"
  value       = aws_s3_bucket.plant_archive.id
}

# Glue Database
resource "aws_glue_catalog_database" "plants_db" {
  name = "c21-boxen-plants-db"
}

# IAM role for Glue Crawler
resource "aws_iam_role" "glue_crawler_role" {
  name = "c21-boxen-glue-crawler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })
}

# Attach AWS managed Glue service policy
resource "aws_iam_role_policy_attachment" "glue_service_policy" {
  role       = aws_iam_role.glue_crawler_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# IAM policy for Glue Crawler to read S3
resource "aws_iam_role_policy" "glue_s3_policy" {
  name = "c21-boxen-glue-s3-policy"
  role = aws_iam_role.glue_crawler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.plant_archive.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.plant_archive.arn
        ]
      }
    ]
  })
}

# Glue Crawler
resource "aws_glue_crawler" "plants_crawler" {
  name          = "c21-boxen-plants-crawler"
  role          = aws_iam_role.glue_crawler_role.arn
  database_name = aws_glue_catalog_database.plants_db.name

  s3_target {
    path = "s3://${aws_s3_bucket.plant_archive.id}/"
  }

  schedule = "cron(15 0 * * ? *)"

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }
}

# Athena Workgroup
resource "aws_athena_workgroup" "plants_workgroup" {
  name = "c21-boxen-plants-workgroup"

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.plant_archive.id}/athena-results/"
    }
  }
}

output "glue_database_name" {
  description = "Glue database name"
  value       = aws_glue_catalog_database.plants_db.name
}

output "athena_workgroup_name" {
  description = "Athena workgroup name"
  value       = aws_athena_workgroup.plants_workgroup.name
}