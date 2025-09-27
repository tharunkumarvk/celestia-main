from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.recommendations_service import healthy_swaps, personalized_recommendations, recipe_generation, recipe_modification, meal_plan_generator
from app.services.user_service import get_user

router = APIRouter()

@router.post("/swaps")
def get_swaps(analysis_data: Dict[str, Any]):
    try:
        swaps = healthy_swaps(analysis_data)
        return {"swaps": swaps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get swaps: {str(e)}")

@router.post("/personalized/{user_id}")
def get_personalized(analysis_data: Dict[str, Any], user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        recs = personalized_recommendations(analysis_data, user.profile)
        return recs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get personalized recommendations: {str(e)}")

@router.post("/recipe")
def generate_recipe(analysis_data: Dict[str, Any]):
    try:
        recipe = recipe_generation(analysis_data)
        return {"recipe": recipe}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recipe: {str(e)}")

@router.post("/recipe/modify")
def modify_recipe(request: Dict[str, Any]):
    try:
        original_recipe = request.get("original_recipe", "")
        user_feedback = request.get("user_feedback", "")
        analysis_data = request.get("analysis_data", {})
        
        if not original_recipe or not user_feedback:
            raise HTTPException(status_code=400, detail="Original recipe and user feedback are required")
        
        modified_recipe = recipe_modification(original_recipe, user_feedback, analysis_data)
        return {"recipe": modified_recipe}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to modify recipe: {str(e)}")

@router.get("/meal_plan/{user_id}")
@router.post("/meal_plan/{user_id}")
def generate_meal_plan(user_id: int, profile: Dict[str, Any] = None, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        used_profile = profile if profile else user.profile
        plan = meal_plan_generator(used_profile)
        return {"plan": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate meal plan: {str(e)}")
