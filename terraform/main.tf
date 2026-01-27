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
    Name        = "c21-boxen-botanical-pipeline-1"
    Environment = "production"
  }
}

# Output the repository URL
output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.lambda_repo.repository_url
}