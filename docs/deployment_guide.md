# Enterprise RAG System - Deployment & Scaling Guide

This guide details instructions for deploying **ApexRAG Enterprise** locally via Docker Compose and scaling in production using Kubernetes (AWS EKS / GCP GKE).

## 1. Local Deployment (Docker Compose)

The fastest way to test the full-stack system locally is using Docker Compose.

```bash
cd deployment
docker-compose up --build -d
```

### Services Deployed:
- **Backend API**: `http://localhost:8000`
- **Frontend Studio**: `http://localhost:8080`
- **API Documentation (Swagger)**: `http://localhost:8000/docs`

## 2. Production Kubernetes Deployment

For high-availability enterprise workloads, deploy to Kubernetes with horizontal pod autoscaling.

```bash
cd deployment/k8s
kubectl apply -f ingress_rbac.yaml
kubectl apply -f service.yaml
kubectl apply -f deployment.yaml
```

### Scaling Considerations:
- **Vector DB Sharding**: In production, replace local FAISS with a distributed vector database like Pinecone, Milvus, or Qdrant to handle billions of embeddings.
- **SQL Sharding**: Connect `SQL_DB_URL` to an AWS Aurora PostgreSQL cluster with read replicas for high-throughput query handling.
- **Pod Autoscaling**: Configure HPA (Horizontal Pod Autoscaler) to scale backend pods when CPU utilization exceeds 70%.

## 3. CI/CD Continuous Integration

Our automated pipeline is defined in `.github/workflows/cicd.yml`.
On every pull request or commit to `main`, GitHub Actions automatically:
1. Provisions Python 3.10 environment.
2. Installs requirements.
3. Executes `pytest` unit test suite covering RBAC policies and RAG routing.
4. Builds the Docker container.
