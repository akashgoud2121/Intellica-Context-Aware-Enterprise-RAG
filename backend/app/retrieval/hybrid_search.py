import re
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.storage.vector_store import vector_store
from app.retrieval.reranker import EnterpriseReranker
from app.storage.db import StructuredFinanceData, StructuredEngineeringLog

class ContextAwareHybridSearcher:
    @staticmethod
    def route_query_intent(query: str) -> str:
        query_lower = query.lower()
        sql_keywords = ["revenue", "profit", "spend", "quarter", "q1", "q2", "q3", "q4", "financials", "million"]
        log_keywords = ["log", "commit", "error", "warning", "service", "timeout", "circuit breaker"]
        
        if any(kw in query_lower for kw in sql_keywords) and ("how much" in query_lower or "what is" in query_lower or "compare" in query_lower or "quarter" in query_lower):
            return "SQL_FINANCE"
        elif any(kw in query_lower for kw in log_keywords):
            return "SQL_ENGINEERING_LOGS"
        else:
            return "UNSTRUCTURED_RAG"

    @staticmethod
    def execute_sql_finance(query: str, db: Session) -> List[Dict[str, Any]]:
        records = db.query(StructuredFinanceData).all()
        results = []
        for r in records:
            results.append({
                "chunk_id": f"finance_sql_{r.id}",
                "filename": "Enterprise SQL Finance DB",
                "data_silo": "finance",
                "text": f"Quarter: {r.quarter} | Revenue: ${r.revenue_millions}M | R&D Spend: ${r.r_and_d_spend_millions}M | Net Profit: ${r.net_profit_millions}M | Status: {r.compliance_status}",
                "relevance_score": 0.95
            })
        return results

    @staticmethod
    def execute_sql_eng_logs(query: str, db: Session) -> List[Dict[str, Any]]:
        records = db.query(StructuredEngineeringLog).all()
        results = []
        for r in records:
            results.append({
                "chunk_id": f"eng_log_{r.id}",
                "filename": "Engineering Service Logs",
                "data_silo": "engineering",
                "text": f"Service: {r.service_name} [{r.log_level}] | Message: {r.message} | Commit: {r.commit_hash} | Time: {r.timestamp}",
                "relevance_score": 0.90
            })
        return results

    @classmethod
    def search(cls, query: str, top_k: int = 5, silo_filter: str = None, db: Session = None) -> Dict[str, Any]:
        intent = cls.route_query_intent(query)
        
        chunks = []
        if intent == "SQL_FINANCE" and db and (not silo_filter or silo_filter == "finance"):
            chunks = cls.execute_sql_finance(query, db)
        elif intent == "SQL_ENGINEERING_LOGS" and db and (not silo_filter or silo_filter == "engineering"):
            chunks = cls.execute_sql_eng_logs(query, db)
        
        # Expanded search depth (top_k * 3) to guarantee project/skill chunks located deeper in resumes are ranked
        expanded_k = top_k * 3
        sem_res = vector_store.semantic_search(query, top_k=expanded_k, silo_filter=silo_filter)
        key_res = vector_store.keyword_search(query, top_k=expanded_k, silo_filter=silo_filter)
        
        reranked_unstructured = EnterpriseReranker.rerank_hybrid_results(sem_res, key_res)
        
        all_results = chunks + reranked_unstructured
        
        seen_ids = set()
        final_results = []
        for res in all_results:
            cid = res["chunk_id"]
            if cid not in seen_ids:
                seen_ids.add(cid)
                final_results.append(res)
            if len(final_results) >= top_k:
                break
                
        return {
            "routed_intent": intent,
            "retrieved_context": final_results
        }
