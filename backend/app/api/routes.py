import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, status
from sqlalchemy.orm import Session
from app.storage.db import get_db, AuditLog
from app.auth.rbac import get_current_user, RBACPolicyEngine, User
from app.ingestion.connectors import IngestionConnectors
from app.ingestion.pipeline import pipeline
from app.retrieval.hybrid_search import ContextAwareHybridSearcher
from app.generation.llm import llm_generator
from app.services.analytics import SystemAnalyticsService

api_router = APIRouter()

@api_router.post("/ingest")
async def ingest_document(
    request: Request,
    file: UploadFile = File(...),
    data_silo: str = Form("engineering"),
    doc_type: str = Form("pdf"), # 'pdf', 'docx', 'pptx', 'json_log', 'csv'
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Secure endpoint for ingesting enterprise data sources"""
    start_time = time.time()
    
    if current_user.role not in ["Executive", "Compliance", "Engineering"]:
        raise HTTPException(status_code=403, detail="RBAC Error: Insufficient clearance to ingest data into enterprise silos.")

    contents = await file.read()
    raw_text = ""
    
    if doc_type == "pdf":
        raw_text = IngestionConnectors.parse_pdf(contents)
        doc_meta = pipeline.process_and_index(file.filename, raw_text, data_silo, doc_type, current_user.username, db)
    elif doc_type == "docx":
        raw_text = IngestionConnectors.parse_docx(contents)
        doc_meta = pipeline.process_and_index(file.filename, raw_text, data_silo, doc_type, current_user.username, db)
    elif doc_type == "pptx":
        raw_text = IngestionConnectors.parse_pptx(contents)
        doc_meta = pipeline.process_and_index(file.filename, raw_text, data_silo, doc_type, current_user.username, db)
    elif doc_type == "json_log":
        chunks = IngestionConnectors.parse_json_log(contents, db)
        from app.storage.vector_store import vector_store
        vector_store.add_documents(chunks)
        raw_text = f"Ingested {len(chunks)} engineering log entries."
    elif doc_type == "csv":
        chunks = IngestionConnectors.parse_csv_finance(contents, db)
        from app.storage.vector_store import vector_store
        vector_store.add_documents(chunks)
        raw_text = f"Ingested {len(chunks)} financial CSV records."
    else:
        try:
            raw_text = contents.decode("utf-8")
        except:
            raw_text = "Binary Data - Ingested as unstructured document."
        pipeline.process_and_index(file.filename, raw_text, data_silo, doc_type, current_user.username, db)

    exec_time = (time.time() - start_time) * 1000
    
    audit = AuditLog(
        username=current_user.username,
        role=current_user.role,
        action="INGEST",
        silo_accessed=data_silo,
        execution_time_ms=exec_time,
        ip_address=request.client.host if request.client else "127.0.0.1",
        success=True
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": f"Successfully ingested {file.filename} into silo '{data_silo}'.", "execution_time_ms": round(exec_time, 2)}

@api_router.get("/query")
def execute_rag_query(
    request: Request,
    query: str,
    silo_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()

    if silo_filter:
        RBACPolicyEngine(required_silo=silo_filter)(request, current_user, db)
    else:
        intent = ContextAwareHybridSearcher.route_query_intent(query)
        if intent == "SQL_FINANCE":
            RBACPolicyEngine(required_silo="finance")(request, current_user, db)
        elif intent == "SQL_ENGINEERING_LOGS":
            RBACPolicyEngine(required_silo="engineering")(request, current_user, db)

    search_results = ContextAwareHybridSearcher.search(query, top_k=5, silo_filter=silo_filter, db=db)
    retrieved_context = search_results["retrieved_context"]

    rag_response = llm_generator.generate_answer(query, retrieved_context)

    exec_time = (time.time() - start_time) * 1000

    audit = AuditLog(
        username=current_user.username,
        role=current_user.role,
        action="QUERY",
        query_text=query,
        silo_accessed=silo_filter or search_results["routed_intent"],
        execution_time_ms=exec_time,
        ip_address=request.client.host if request.client else "127.0.0.1",
        success=True
    )
    db.add(audit)
    db.commit()

    return {
        "query": query,
        "routed_intent": search_results["routed_intent"],
        "execution_time_ms": round(exec_time, 2),
        "user_context": {
            "username": current_user.username,
            "role": current_user.role,
            "department": current_user.department
        },
        "response": rag_response
    }

@api_router.get("/analytics")
def get_system_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["Executive", "Compliance", "Engineering"]:
        raise HTTPException(status_code=403, detail="Access denied. Analytics dashboard requires Executive or Compliance clearance.")
    return SystemAnalyticsService.get_dashboard_metrics(db)
