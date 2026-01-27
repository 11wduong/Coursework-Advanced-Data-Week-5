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

# EventBridge rule to trigger Lambda every minute
resource "aws_cloudwatch_event_rule" "every_minute" {
  name                = "c21-boxen-plant-load-every-minute"
  description         = "Trigger plant load pipeline every minute"
  schedule_expression = "rate(1 minute)"
}

# EventBridge target
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.every_minute.name
  target_id = "plant-load-lambda"
  arn       = aws_lambda_function.plant_load.arn
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.plant_load.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_minute.arn
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