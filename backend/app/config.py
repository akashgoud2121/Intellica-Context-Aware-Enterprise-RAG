import os
from typing import Dict, List, Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Enterprise RAG System API"
    VERSION: str = "1.0.0"
    DEBUG_MODE: bool = True
    
    # Security / SSO / JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-enterprise-key-secure-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # Storage Settings
    STORAGE_DIR: str = os.path.join(os.path.expanduser("~"), ".enterprise_rag_storage")
    VECTOR_STORE_PATH: str = os.path.join(STORAGE_DIR, "faiss_index")
    SQL_DB_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(STORAGE_DIR, 'enterprise.db')}")

    # Embeddings / LLM Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    LLM_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "mock-enterprise-api-key-for-local-execution")

    # RBAC Policies Matrix
    # Roles: Executive, Engineering, HR, Finance, Compliance
    ROLES_PERMISSIONS: Dict[str, Dict[str, Any]] = {
        "Executive": {
            "allowed_silos": ["finance", "hr", "engineering", "compliance", "public"],
            "max_query_limit": 1000,
            "security_clearance": "Top Secret"
        },
        "Engineering": {
            "allowed_silos": ["engineering", "public"],
            "max_query_limit": 500,
            "security_clearance": "Confidential"
        },
        "HR": {
            "allowed_silos": ["hr", "public"],
            "max_query_limit": 300,
            "security_clearance": "Restricted"
        },
        "Finance": {
            "allowed_silos": ["finance", "public"],
            "max_query_limit": 300,
            "security_clearance": "Secret"
        },
        "Compliance": {
            "allowed_silos": ["compliance", "hr", "finance", "public"],
            "max_query_limit": 500,
            "security_clearance": "Secret"
        },
        "Guest": {
            "allowed_silos": ["public"],
            "max_query_limit": 50,
            "security_clearance": "Unclassified"
        }
    }

    class Config:
        env_file = ".env"

settings = Settings()

# Ensure storage directories exist
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "documents"), exist_ok=True)
