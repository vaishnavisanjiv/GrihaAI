from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, projects, floor_plans, analysis, health, reports, assistant

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BuildGuard AI",
    description="Intelligent Building Layout Compliance and Safety Analysis Platform",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"name": "BuildGuard AI API", "status": "ok", "docs": "/docs"}

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.FRONTEND_URL.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(floor_plans.router, prefix="/api/floor-plans", tags=["floor-plans"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(assistant.router, prefix="/api/assistant", tags=["assistant"])

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True
    )
