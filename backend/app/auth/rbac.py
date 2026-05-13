import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from app.config import settings
from app.storage.db import get_db, User, AuditLog

auth_router = APIRouter()

class TokenData:
    def __init__(self, username: str, role: str):
        self.username = username
        self.role = role

def authenticate_sso_ldap(username: str, db: Session) -> User:
    """Mock Enterprise Single Sign-On (LDAP / Active Directory Integration)"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid LDAP credentials or SSO token")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive or disabled")
    return user

def get_current_user(x_username: str = Header(default="ceo_alice"), db: Session = Depends(get_db)) -> User:
    """Extract user from simulated SSO header or token"""
    return authenticate_sso_ldap(x_username, db)

class RBACPolicyEngine:
    def __init__(self, required_silo: Optional[str] = None):
        self.required_silo = required_silo

    def __call__(self, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        role = current_user.role
        permissions = settings.ROLES_PERMISSIONS.get(role, settings.ROLES_PERMISSIONS["Guest"])
        allowed_silos = permissions["allowed_silos"]
        
        # Check silo access
        if self.required_silo and self.required_silo not in allowed_silos:
            # Log Unauthorized attempt
            audit = AuditLog(
                username=current_user.username,
                role=current_user.role,
                action="UNAUTHORIZED_ACCESS",
                silo_accessed=self.required_silo,
                execution_time_ms=0.0,
                ip_address=request.client.host if request.client else "127.0.0.1",
                success=False
            )
            db.add(audit)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"RBAC Policy Violation: Role '{role}' does not have access to data silo '{self.required_silo}'."
            )
        return current_user

@auth_router.get("/users/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    permissions = settings.ROLES_PERMISSIONS.get(current_user.role, settings.ROLES_PERMISSIONS["Guest"])
    return {
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "department": current_user.department,
        "clearance": permissions["security_clearance"],
        "allowed_silos": permissions["allowed_silos"]
    }

@auth_router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"username": u.username, "role": u.role, "department": u.department} for u in users]
