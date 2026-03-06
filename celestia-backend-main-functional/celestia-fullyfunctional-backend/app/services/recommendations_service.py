import json
from typing import Any, Dict, List

import google.generativeai as genai
from app.config import settings

from .analysis_service import clean_json_response

genai.configure(api_key=settings.google_api_key)
gemini_model = genai.GenerativeModel("models/gemini-2.0-flash")

def healthy_swaps(analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    prompt = f"""You are a nutrition expert specializing in Indian cuisine. Suggest culturally appropriate healthy swaps for {json.dumps(analysis_data.get('items', []))}. 
    
    INDIAN HEALTHY SWAPS EXPERTISE:
    - Prioritize traditional Indian healthy alternatives (e.g., brown rice over white rice, ragi over wheat)
    - Suggest cooking method improvements (steamed idli over fried vada, grilled tandoor over deep-fried)
    - Recommend traditional superfoods (quinoa, millets like bajra/jowar, amaranth)
    - Consider regional healthy options (coconut oil in South India, mustard oil in East India)
    - Suggest spice-based health improvements (turmeric, ginger, garlic, fenugreek)
    - Maintain authentic Indian flavors while improving nutrition
    - Consider vegetarian/vegan Indian alternatives
    
    CRITICAL: Return ONLY valid JSON with 'swaps' array. Each swap object must have exactly these string fields:
    - 'original': name of current food item (string only)
    - 'swap': name of healthier alternative (string only)  
    - 'reason': brief health benefit explanation (string only)
    - 'indian_benefit': cultural/traditional benefit (string only)
    
    Example format:
    {{
        "swaps": [
            {{
                "original": "White rice",
                "swap": "Brown rice", 
                "reason": "Higher fiber and nutrients",
                "indian_benefit": "Traditional choice in South India"
            }}
        ]
    }}"""
    
    try:
        response = gemini_model.generate_content(prompt)
        data = clean_json_response(response.text)
        
        if not data or 'swaps' not in data:
            print(f"Invalid swaps response format: {data}")
            return []
        
        # Validate and sanitize each swap
        validated_swaps = []
        for swap in data.get('swaps', []):
            if isinstance(swap, dict):
                validated_swap = {
                    'original': str(swap.get('original', 'Unknown food')),
                    'swap': str(swap.get('swap', 'Healthier alternative')),
                    'reason': str(swap.get('reason', 'Better nutritional profile')),
                    'indian_benefit': str(swap.get('indian_benefit', 'Culturally appropriate'))
                }
                validated_swaps.append(validated_swap)
            else:
                print(f"Invalid swap format: {swap}")
        
        return validated_swaps
        
    except Exception as e:
        print(f"Healthy swaps error: {e}")
        # Return a fallback swap suggestion
        return [{
            'original': 'Current choice',
            'swap': 'Healthier alternative', 
            'reason': 'Better nutrition profile',
            'indian_benefit': 'Follows traditional Indian nutrition principles'
        }]

def personalized_recommendations(analysis_data: Dict[str, Any], user_profile: Dict[str, Any]) -> Dict[str, Any]:
    prompt = f"""You are a nutrition expert specializing in Indian cuisine and lifestyle. Provide personalized recommendations for {json.dumps(analysis_data)} 
    based on user profile {json.dumps(user_profile)} (goals, allergies, diet). 
    
    INDIAN PERSONALIZED NUTRITION:
    - Consider Indian lifestyle patterns (meal timing, festival foods, regional preferences)
    - Account for common Indian dietary restrictions (vegetarian, Jain, regional customs)
    - Suggest Indian seasonal foods and their benefits
    - Include Ayurvedic principles where relevant (body constitution, food combinations)
    - Consider Indian cooking methods and their health impacts
    - Recommend traditional Indian remedies and functional foods
    - Address common Indian nutritional deficiencies (iron, B12, vitamin D)
    
    Include allergen alerts, personalized advice, and Indian-specific recommendations. Format as JSON with 'recommendations', 'alerts', 'indian_tips', 'seasonal_advice' fields."""
    
    try:
        response = gemini_model.generate_content(prompt)
        result = clean_json_response(response.text)
        return result if result else {"recommendations": [], "alerts": []}
    except Exception as e:
        print(f"Personalized recommendations error: {e}")
        return {"recommendations": [], "alerts": []}

def recipe_generation(analysis_data: Dict[str, Any]) -> str:
    prompt = f"""You are a chef specializing in healthy Indian cuisine. Generate a healthy Indian recipe using detected items from {json.dumps(analysis_data)}. 

    CRITICAL REQUIREMENT: ALL TEXT MUST BE IN ENGLISH ONLY. No Hindi words or phrases should be used anywhere in the response.
    
    INDIAN RECIPE EXPERTISE:
    - Create authentic Indian recipes with proper spice combinations
    - Include traditional cooking techniques (tempering/tadka, slow cooking, steaming)
    - Suggest regional variations and accompaniments
    - Use traditional Indian ingredients and cooking vessels where appropriate
    - Include health benefits of Indian spices and ingredients
    - Provide cooking tips specific to Indian cuisine
    - Consider vegetarian/vegan options prominently
    
    Format the response EXACTLY as follows with these EXACT headings:
    ## [Recipe Title]
    ### Ingredients
    - ingredient 1
    - ingredient 2
    
    ### Instructions
    1. step 1
    2. step 2
    
    ### Nutrition Info
    [Nutrition details]
    
    ### Health Benefits
    [Health benefits]
    
    ### Regional Variations
    [Regional variations]
    
    Make it appealing, authentic, and easy to follow for Indian home cooking. Remember: Use ONLY English language throughout."""
    
    try:
        response = gemini_model.generate_content(prompt)
        if not response or not response.text:
            return "## Recipe Generation Failed\n### Ingredients\n- No ingredients available\n### Instructions\n1. Recipe generation failed\n### Nutrition Info\nNot available\n### Health Benefits\nNot available\n### Regional Variations\nNot available"
        
        # Ensure response has all required sections
        text = response.text
        required_sections = ['## ', '### Ingredients', '### Instructions', '### Nutrition Info', '### Health Benefits', '### Regional Variations']
        
        # Add any missing sections
        for section in required_sections:
            if section not in text:
                if section == '## ':
                    text = f"## Generated Recipe\n{text}"
                else:
                    text = f"{text}\n{section}\nNot available"
        
        return text
        
    except Exception as e:
        print(f"Recipe generation error: {e}")
        return "## Recipe Generation Failed\n### Ingredients\n- Error occurred\n### Instructions\n1. Unable to generate recipe\n### Nutrition Info\nNot available\n### Health Benefits\nNot available\n### Regional Variations\nNot available"

def recipe_modification(original_recipe: str, user_feedback: str, analysis_data: Dict[str, Any]) -> str:
    prompt = f"""You are a chef specializing in healthy Indian cuisine. The user has provided feedback on a recipe and wants modifications.

    CRITICAL REQUIREMENT: ALL TEXT MUST BE IN ENGLISH ONLY. No Hindi words or phrases should be used anywhere in the response.

    Original Recipe:
    {original_recipe}

    User Feedback/Request:
    {user_feedback}

    Original Food Analysis:
    {json.dumps(analysis_data)}

    MODIFICATION GUIDELINES:
    - Understand the user's preference (sweet, spicy, healthy, quick, etc.)
    - Modify the recipe accordingly while maintaining Indian authenticity
    - If user wants something completely different, suggest a new Indian dish that matches their mood
    - Keep the same format as the original recipe
    - Explain what changes were made and why
    - Maintain nutritional balance where possible

    Generate the modified recipe in the same format as before, with clear explanations of changes made.
    Remember: Use ONLY English language throughout."""
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Recipe modification error: {e}")
        return "Recipe modification failed. Please try again later."

def meal_plan_generator(user_profile: Dict[str, Any]) -> str:
    prompt = f"""You are a nutrition expert specializing in Indian meal planning. Generate a weekly Indian meal plan aligned with user profile {json.dumps(user_profile)}. 
    
    INDIAN MEAL PLANNING EXPERTISE:
    - Follow traditional Indian meal patterns (breakfast, lunch, evening snack, dinner)
    - Include regional variety (North Indian, South Indian, Bengali, Gujarati, etc.)
    - Consider Indian seasonal availability and festivals
    - Balance traditional foods with modern nutritional needs
    - Include proper Indian food combinations and meal timing
    - Suggest traditional Indian beverages (buttermilk, herbal teas, etc.)
    - Account for Indian cooking methods and preparation time
    - Include vegetarian options prominently with complete protein combinations
    
    Format as Markdown with ## Weekly Indian Meal Plan, then ### Day 1, etc., with traditional Indian meals, calories, and regional notes. 
    Keep it realistic, varied, culturally authentic, and suitable for Indian households."""
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Meal plan generation error: {e}")
        return "Meal plan generation failed. Please try again later."
