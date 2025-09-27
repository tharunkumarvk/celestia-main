from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Date, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    profile = Column(JSON, default={})
    daily_goals = Column(JSON, default={})  # Daily calorie/macro goals
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    meals = relationship("Meal", back_populates="user")
    daily_summaries = relationship("DailySummary", back_populates="user")

class Meal(Base):
    __tablename__ = "meals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    analysis_data = Column(JSON, default={})
    portion_estimates = Column(JSON, default={})
    nutrition_summary = Column(JSON, default={})
    recommendations = Column(JSON, default={})
    meal_type = Column(String, nullable=True)  # breakfast, lunch, dinner, snack
    upload_date = Column(Date, server_default=func.current_date())
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    day_of_week = Column(String, nullable=True)  # Monday, Tuesday, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="meals")

class DailySummary(Base):
    __tablename__ = "daily_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, nullable=False)
    total_calories = Column(Float, default=0.0)
    total_protein = Column(Float, default=0.0)
    total_carbs = Column(Float, default=0.0)
    total_fat = Column(Float, default=0.0)
    total_fiber = Column(Float, default=0.0)
    meals_count = Column(Integer, default=0)
    goal_calories_achieved = Column(Boolean, default=False)
    goal_protein_achieved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="daily_summaries")
