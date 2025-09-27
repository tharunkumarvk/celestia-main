from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import sessions, analysis, users, nutrition, recommendations, dashboard, agentic_ai
from app.config import settings
from app.database import Base, engine
from app.models.db_models import User, Meal, DailySummary
from app.models.agentic_models import (
    ConversationMemory, HealthAlert, SmartNotification, MealPlan, MealPlanItem,
    UserBehaviorPattern, PredictiveInsight
)
from app.routers import agent

app = FastAPI(title="Smart Food Analyzer API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8000",
        "http://10.0.2.2:8000",  # Android emulator
        "http://YOUR_COMPUTER_IP:8000",  # Replace with your IP
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://your-frontend-domain.netlify.app",  # Replace with your actual domain
        "*"  # Remove in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized on startup")

app.include_router(sessions.router, prefix="/sessions")
app.include_router(analysis.router, prefix="/analysis")
app.include_router(users.router, prefix="/users")
app.include_router(nutrition.router, prefix="/nutrition")
app.include_router(recommendations.router, prefix="/recommendations")
app.include_router(agent.router, prefix="/agent")
app.include_router(dashboard.router, prefix="/dashboard")
app.include_router(agentic_ai.router)  # Agentic AI features with /agentic prefix

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Food Analyzer API"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}
