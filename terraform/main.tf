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