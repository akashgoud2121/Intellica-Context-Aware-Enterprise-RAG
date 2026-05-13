output "s3_bucket_arn" {
  value = aws_s3_bucket.rag_data_lake.arn
}

output "eks_cluster_endpoint" {
  value = aws_eks_cluster.rag_cluster.endpoint
}
