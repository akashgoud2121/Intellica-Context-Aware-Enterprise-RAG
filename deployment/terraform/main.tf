provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "rag_data_lake" {
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_lifecycle_configuration" "rag_lifecycle" {
  bucket = aws_s3_bucket.rag_data_lake.id

  rule {
    id     = "archive-infrequent-access"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}

resource "aws_eks_cluster" "rag_cluster" {
  name     = "enterprise-rag-cluster"
  role_arn = var.eks_role_arn

  vpc_config {
    subnet_ids = var.subnet_ids
  }
}
