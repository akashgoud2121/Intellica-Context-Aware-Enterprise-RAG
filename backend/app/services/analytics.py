from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.storage.db import AuditLog, DocumentMetadata

class SystemAnalyticsService:
    @staticmethod
    def get_dashboard_metrics(db: Session) -> Dict[str, Any]:
        total_queries = db.query(AuditLog).filter(AuditLog.action == "QUERY").count()
        avg_latency = db.query(func.avg(AuditLog.execution_time_ms)).filter(AuditLog.action == "QUERY").scalar() or 0.0
        rbac_violations = db.query(AuditLog).filter(AuditLog.action == "UNAUTHORIZED_ACCESS").count()
        total_docs = db.query(DocumentMetadata).count()
        
        # Breakdown by role
        role_breakdown = db.query(AuditLog.role, func.count(AuditLog.id)).group_by(AuditLog.role).all()
        
        # Recent audit logs
        recent_logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(15).all()
        
        return {
            "system_health": {
                "uptime_status": "Operational",
                "active_silos": ["finance", "engineering", "hr", "compliance", "public"],
                "total_documents_ingested": total_docs,
                "vector_index_status": "Healthy - 100% Synced"
            },
            "performance_metrics": {
                "total_queries_served": total_queries,
                "average_response_time_ms": round(avg_latency, 2),
                "system_throughput_qpm": round(total_queries / 60.0, 2),
                "rbac_unauthorized_attempts": rbac_violations
            },
            "role_activity": [{"role": r[0], "count": r[1]} for r in role_breakdown],
            "audit_trail": [{
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "username": log.username,
                "role": log.role,
                "action": log.action,
                "silo_accessed": log.silo_accessed,
                "execution_time_ms": round(log.execution_time_ms, 2),
                "success": log.success
            } for log in recent_logs]
        }
