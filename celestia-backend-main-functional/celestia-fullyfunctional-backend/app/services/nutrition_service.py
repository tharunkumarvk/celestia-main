from typing import Dict, Any
import json
import google.generativeai as genai
from app.config import settings
from .analysis_service import clean_json_response

genai.configure(api_key=settings.google_api_key)
gemini_model = genai.GenerativeModel("models/gemini-2.0-flash")

def nutrition_lookup(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    prompt = f"""You are a nutrition expert specializing in Indian cuisine. Provide detailed nutrition facts using ICMR (Indian Council of Medical Research) guidelines and Indian food composition tables for items: {json.dumps(analysis_data.get('items', []))}. 
    
    INDIAN NUTRITION EXPERTISE:
    - Use ICMR nutritional values for Indian foods when available
    - Consider traditional Indian cooking methods and their nutritional impact
    - Include micronutrients important in Indian diet (iron, calcium, vitamin B12, folate)
    - Account for regional variations in preparation and ingredients
    - Consider bioavailability of nutrients in Indian cooking context (e.g., iron absorption with vitamin C from lemon/tomatoes)
    - Include traditional nutritional benefits (turmeric's curcumin, ghee's fat-soluble vitamins, etc.)
    
    Include totals and micronutrients. Format as structured JSON with 'items' array and 'totals' object for better display."""
    
    try:
        response = gemini_model.generate_content(prompt)
        result = clean_json_response(response.text)
        return result if result else {"items": [], "totals": {}}
    except Exception as e:
        print(f"Nutrition lookup error: {e}")
        return {"items": [], "totals": {}}

def detailed_nutrition_breakdown(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    prompt = f"""You are a nutrition expert specializing in Indian cuisine. Provide a comprehensive breakdown of nutrients for the analyzed food items: {json.dumps(analysis_data.get('items', []))}.

    CRITICAL REQUIREMENT: ALL TEXT MUST BE IN ENGLISH ONLY.

    Create detailed nutrient postcards with the following structure:
    
    NUTRIENT CATEGORIES TO ANALYZE:
    1. Macronutrients (Carbohydrates, Proteins, Fats)
    2. Vitamins (A, B-complex, C, D, E, K)
    3. Minerals (Iron, Calcium, Magnesium, Zinc, Potassium, Sodium)
    4. Fiber and Water content
    5. Antioxidants and Phytonutrients
    6. Indian-specific nutrients (Curcumin from turmeric, etc.)

    For each nutrient category, provide:
    - Total amount present
    - Percentage of daily recommended intake (based on ICMR guidelines)
    - Health benefits specific to Indian lifestyle
    - Food sources contributing most to this nutrient
    - Deficiency risks and symptoms
    - Traditional Indian remedies or foods to boost this nutrient

    Format as JSON with 'nutrient_cards' array containing objects with:
    - 'category': nutrient category name
    - 'nutrients': array of individual nutrients in this category
    - 'total_amount': combined amount
    - 'daily_value_percentage': % of daily recommended intake
    - 'health_benefits': array of health benefits
    - 'top_sources': foods contributing most
    - 'deficiency_info': risks and symptoms
    - 'indian_boosters': traditional ways to increase this nutrient
    - 'color_theme': suggested color for UI display"""
    
    try:
        response = gemini_model.generate_content(prompt)
        result = clean_json_response(response.text)
        return result if result else {"nutrient_cards": []}
    except Exception as e:
        print(f"Detailed nutrition breakdown error: {e}")
        return {"nutrient_cards": []}
