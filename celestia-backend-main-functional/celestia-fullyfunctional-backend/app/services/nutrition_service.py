import json
from typing import Any, Dict

import google.generativeai as genai
from app.config import settings

from .analysis_service import clean_json_response

genai.configure(api_key=settings.google_api_key)
gemini_model = genai.GenerativeModel("models/gemini-2.0-flash")

def nutrition_lookup(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    items = analysis_data.get('items', [])
    clarifications = analysis_data.get('clarifications', '')
    
    # Enhanced prompt for more accurate analysis
    clarification_text = f"\n\nADDITIONAL CONTEXT: {clarifications}" if clarifications else ""
    
    prompt = f"""You are a nutrition expert specializing in Indian cuisine. Analyze these food items with their specified quantities and provide precise nutritional information using ICMR guidelines and Indian food composition tables.

    FOOD ITEMS TO ANALYZE: {json.dumps(items)}
    {clarification_text}

    ANALYSIS REQUIREMENTS:
    - Use ICMR (Indian Council of Medical Research) nutritional values when available
    - Consider traditional Indian cooking methods and preparation styles
    - Account for regional variations and common ingredients used in Indian cooking
    - Include bioavailability factors (e.g., iron absorption enhanced by vitamin C from lemon/tomatoes)
    - Consider traditional nutritional benefits (turmeric's curcumin, ghee's fat-soluble vitamins, etc.)
    - Be precise with portion sizes and their nutritional impact

    For each food item, carefully analyze:
    1. The specific food name and any regional variations
    2. The exact quantity specified and convert to standard nutritional portions
    3. Cooking method implications (if mentioned or implied)
    4. Nutritional density based on Indian food composition data

    MANDATORY JSON RESPONSE STRUCTURE:
    {{
        "items": [
            {{
                "name": "exact food name as analyzed",
                "quantity": "standardized portion description", 
                "calories": precise_numerical_value,
                "protein": precise_grams_value,
                "carbs": precise_grams_value,
                "fat": precise_grams_value,
                "confidence": 95
            }}
        ],
        "totals": {{
            "calories": exact_sum_of_all_calories,
            "protein": exact_sum_of_all_protein,
            "carbs": exact_sum_of_all_carbs,  
            "fat": exact_sum_of_all_fat
        }},
        "total_calories": exact_sum_of_all_calories,
        "total_protein": exact_sum_of_all_protein,
        "total_carbs": exact_sum_of_all_carbs,
        "total_fat": exact_sum_of_all_fat
    }}

    CRITICAL: 
    - ALL numerical values MUST be numbers, not strings
    - Totals MUST equal the exact sum of individual item values
    - Use Indian nutritional standards and portion contexts
    - Account for cooking losses/gains in nutritional values"""
    
    try:
        response = gemini_model.generate_content(prompt)
        result = clean_json_response(response.text)
        
        # Validate and enhance the result
        if result and isinstance(result, dict):
            # Ensure items array exists
            items = result.get('items', [])
            
            # Calculate totals if missing or incorrect
            total_calories = sum(item.get('calories', 0) for item in items)
            total_protein = sum(item.get('protein', 0) for item in items)
            total_carbs = sum(item.get('carbs', 0) for item in items)
            total_fat = sum(item.get('fat', 0) for item in items)
            
            # Ensure the response has the expected structure
            enhanced_result = {
                'items': items,
                'totals': {
                    'calories': total_calories,
                    'protein': total_protein,
                    'carbs': total_carbs,
                    'fat': total_fat
                },
                'total_calories': total_calories,
                'total_protein': total_protein,
                'total_carbs': total_carbs,
                'total_fat': total_fat
            }
            
            return enhanced_result
        else:
            # Fallback with original items if available
            original_items = analysis_data.get('items', [])
            return {
                "items": original_items,
                "totals": {
                    "calories": sum(item.get('calories', 0) for item in original_items),
                    "protein": sum(item.get('protein', 0) for item in original_items),
                    "carbs": sum(item.get('carbs', 0) for item in original_items),
                    "fat": sum(item.get('fat', 0) for item in original_items)
                },
                "total_calories": sum(item.get('calories', 0) for item in original_items),
                "total_protein": sum(item.get('protein', 0) for item in original_items),
                "total_carbs": sum(item.get('carbs', 0) for item in original_items),
                "total_fat": sum(item.get('fat', 0) for item in original_items)
            }
    except Exception as e:
        print(f"Nutrition lookup error: {e}")
        # Fallback with original items
        original_items = analysis_data.get('items', [])
        return {
            "items": original_items,
            "totals": {
                "calories": sum(item.get('calories', 0) for item in original_items),
                "protein": sum(item.get('protein', 0) for item in original_items),
                "carbs": sum(item.get('carbs', 0) for item in original_items),
                "fat": sum(item.get('fat', 0) for item in original_items)
            },
            "total_calories": sum(item.get('calories', 0) for item in original_items),
            "total_protein": sum(item.get('protein', 0) for item in original_items),
            "total_carbs": sum(item.get('carbs', 0) for item in original_items),
            "total_fat": sum(item.get('fat', 0) for item in original_items)
        }

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
