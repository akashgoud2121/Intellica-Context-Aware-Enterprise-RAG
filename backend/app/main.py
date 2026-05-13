from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.config import settings
from app.storage.db import init_db
from app.auth.rbac import auth_router
from app.api.routes import api_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Secure, Scalable, Context-Aware RAG System with Strict RBAC Enforcement."
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

instrumentator = Instrumentator().instrument(app)

@app.on_event("startup")
def on_startup():
    init_db()
    instrumentator.expose(app)


app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication & RBAC"])
app.include_router(api_router, prefix="/api/v1", tags=["RAG Core"])

@app.get("/")
def root():
    return {
        "system": settings.APP_NAME,
        "status": "Operational",
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
