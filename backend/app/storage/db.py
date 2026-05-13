from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from app.config import settings

engine = create_engine(settings.SQL_DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="Guest")
    department = Column(String)
    is_active = Column(Boolean, default=True)

class DocumentMetadata(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    data_silo = Column(String, index=True) # e.g., 'finance', 'engineering'
    doc_type = Column(String) # 'pdf', 'sql', 'json_log', 'csv'
    uploaded_by = Column(String)
    upload_time = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text)
    file_path = Column(String)
    is_encrypted = Column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    username = Column(String, index=True)
    role = Column(String)
    action = Column(String) # 'QUERY', 'INGEST', 'AUTH_SUCCESS', 'UNAUTHORIZED_ACCESS'
    query_text = Column(Text, nullable=True)
    silo_accessed = Column(String, nullable=True)
    execution_time_ms = Column(Float)
    ip_address = Column(String)
    success = Column(Boolean)

class StructuredFinanceData(Base):
    __tablename__ = "finance_records"
    id = Column(Integer, primary_key=True, index=True)
    quarter = Column(String, index=True)
    revenue_millions = Column(Float)
    r_and_d_spend_millions = Column(Float)
    net_profit_millions = Column(Float)
    compliance_status = Column(String)

class StructuredEngineeringLog(Base):
    __tablename__ = "engineering_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    service_name = Column(String, index=True)
    log_level = Column(String, index=True)
    message = Column(Text)
    commit_hash = Column(String)

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Seed default enterprise users if empty
    db = SessionLocal()
    if db.query(User).count() == 0:
        default_users = [
            User(username="ceo_alice", email="alice@enterprise.com", hashed_password="hashed_pwd_alice", role="Executive", department="Management"),
            User(username="lead_bob", email="bob@enterprise.com", hashed_password="hashed_pwd_bob", role="Engineering", department="Engineering"),
            User(username="hr_clara", email="clara@enterprise.com", hashed_password="hashed_pwd_clara", role="HR", department="Human Resources"),
            User(username="fin_david", email="david@enterprise.com", hashed_password="hashed_pwd_david", role="Finance", department="Finance"),
            User(username="comp_eve", email="eve@enterprise.com", hashed_password="hashed_pwd_eve", role="Compliance", department="Legal"),
            User(username="guest_frank", email="frank@enterprise.com", hashed_password="hashed_pwd_frank", role="Guest", department="Contractor")
        ]
        db.add_all(default_users)
        
        # Seed finance records
        finance_records = [
            StructuredFinanceData(quarter="Q1 2025", revenue_millions=145.5, r_and_d_spend_millions=35.0, net_profit_millions=28.4, compliance_status="Passed"),
            StructuredFinanceData(quarter="Q2 2025", revenue_millions=160.2, r_and_d_spend_millions=40.0, net_profit_millions=34.1, compliance_status="Passed"),
            StructuredFinanceData(quarter="Q3 2025", revenue_millions=155.0, r_and_d_spend_millions=38.5, net_profit_millions=31.0, compliance_status="Audited - Clear"),
            StructuredFinanceData(quarter="Q4 2025", revenue_millions=180.8, r_and_d_spend_millions=45.0, net_profit_millions=42.6, compliance_status="Passed")
        ]
        db.add_all(finance_records)
        
        # Seed engineering logs
        eng_logs = [
            StructuredEngineeringLog(service_name="auth-service", log_level="INFO", message="LDAP SSO sync completed successfully across 400 nodes.", commit_hash="a8f9c1d"),
            StructuredEngineeringLog(service_name="rag-pipeline", log_level="WARNING", message="Vector index FAISS shard #3 rebalancing triggered.", commit_hash="b43e810"),
            StructuredEngineeringLog(service_name="payment-gateway", log_level="ERROR", message="Timeout connecting to bank API. Retrying circuit breaker.", commit_hash="c109f52")
        ]
        db.add_all(eng_logs)
        
        db.commit()
    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
