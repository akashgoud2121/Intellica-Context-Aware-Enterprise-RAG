# Cost Analysis & Cloud Optimization Report

Building an enterprise-scale RAG system requires careful balancing of compute, storage, and API consumption expenses. This report details cost estimates and architectural optimizations for running **ApexRAG Enterprise**.

## 1. Estimated Monthly Infrastructure Costs (AWS / GCP)

| Resource Category | Service / Configuration | Monthly Est. Cost |
| :--- | :--- | :--- |
| **Compute (EKS / GKE)** | 3x `c6i.2xlarge` instances (Backend + Embedding pods) | $360.00 |
| **Vector Storage** | Pinecone Standard / Managed Milvus (10M Vectors) | $150.00 |
| **Structured DB** | AWS Aurora Serverless v2 (PostgreSQL) | $120.00 |
| **Data Lake Storage** | S3 Standard (1 TB Active Documents) | $23.00 |
| **Cold Storage Archive** | S3 Glacier Flexible Archive (10 TB Audit & Historic) | $36.00 |
| **LLM Inference API** | OpenAI GPT-4-Turbo / Claude 3 (Est. 500k Queries/mo) | $850.00 |
| **Total Estimated Cost** | | **$1,539.00 / month** |

## 2. Cost Optimization Strategies Implemented

### Serverless & Auto-scaling
- By utilizing AWS Aurora Serverless v2, database compute scales down to 0.5 ACUs during idle night-time hours, saving up to 60% compared to provisioned instances.

### Lifecycle Storage Policies (S3 Glacier)
- Configured in Terraform (`main.tf`), ingested raw documents transition to **S3 Glacier** after 90 days of inactivity. This reduces long-term unstructured data silo storage costs by 85%.

### Hybrid Search Caching & Local Embedding
- Using open-source sentence-transformers (`all-MiniLM-L6-v2`) locally within Kubernetes pods eliminates external embedding API costs entirely (saving approx. $200/mo on large ingestion pipelines).
- Semantic caching layers can bypass LLM generation entirely for frequent queries.
