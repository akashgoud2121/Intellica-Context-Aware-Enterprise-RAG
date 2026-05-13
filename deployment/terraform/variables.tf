variable "aws_region" {
  default = "us-east-1"
}

variable "s3_bucket_name" {
  default = "enterprise-rag-secure-datalake-prod"
}

variable "eks_role_arn" {
  description = "IAM Role ARN for EKS Cluster"
  type        = string
  default     = "arn:aws:iam::123456789012:role/EKSClusterRole"
}

variable "subnet_ids" {
  description = "VPC Subnet IDs"
  type        = list(string)
  default     = ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"]
}
