# Intellica: Context-Aware Enterprise RAG Architecture

**Intellica** is a production-grade, highly secure, and context-aware Retrieval-Augmented Generation (RAG) architecture built to access large-scale enterprise data silos while enforcing strict Role-Based Access Control (RBAC).

---

## 🌟 Key Features

- 🔐 **Strict RBAC Enforcement**: Role-based access control policies mapping simulated LDAP/SSO user profiles to specific data clearance levels (Executive, Engineering, HR, Finance, Compliance).
- 🔀 **Context-Aware Hybrid Routing**: Intelligently determines user intent. Analytical financial queries are routed directly to structured SQL databases, while semantic knowledge queries search FAISS and BM25 vector spaces.
- 📁 **Multi-Format Ingestion Connectors**: Native parsers supporting PowerPoint (`.pptx`), Word documents (`.docx`), PDF reports, JSON engineering logs, and structured financial CSVs.
- 📊 **Uncertainty Quantification & Citations**: Calculates statistical confidence scores for generated answers to minimize hallucinations, and displays explicit citation references linking to original documents.
- 🚀 **Cloud & Container Ready**: Fully containerized with Docker Compose, Kubernetes manifests for horizontal pod autoscaling, and Terraform IaC for AWS EKS & S3 Glacier lifecycle archiving.
- 📈 **Real-time Analytics Dashboard**: Built-in monitoring for query latencies, system throughput (QPM), and unauthorized RBAC access attempt logging.

---

## 📁 Repository Structure

```
├── backend/                  # FastAPI Application, FAISS Vector Store, RBAC Policy Engine
├── frontend/                 # Premium Executive Light Glassmorphic Studio UI
├── deployment/               # Docker Compose, Kubernetes Manifests, Terraform IaC
├── docs/                     # Architecture, Deployment Guide, Cost Analysis, Test Reports
└── .github/workflows/        # Automated CI/CD GitHub Actions Pipeline
```

---

## 🚀 Quickstart Guide

### 1. Run Locally with Docker Compose

Ensure Docker is installed on your workstation.

```bash
cd deployment
docker-compose up --build -d
```

- **Frontend Studio UI**: [http://localhost:8080](http://localhost:8080)
- **Backend API Gateway**: [http://localhost:8000](http://localhost:8000)
- **API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Run Local Test Suite

```bash
cd backend
pip install -r requirements.txt
pytest tests/
```

---

## 📖 Comprehensive Documentation Links

- [System Architecture & Data Flows](docs/system_architecture.md)
- [Deployment & Scaling Guide](docs/deployment_guide.md)
- [Cost Analysis & Optimization Report](docs/cost_analysis_report.md)
- [Testing & Validation Report](docs/testing_validation_report.md)
