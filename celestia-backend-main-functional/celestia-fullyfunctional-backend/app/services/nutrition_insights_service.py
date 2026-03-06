import json
from typing import Any, Dict

import google.generativeai as genai
from app.config import settings

from .analysis_service import clean_json_response

genai.configure(api_key=settings.google_api_key)
gemini_model = genai.GenerativeModel("models/gemini-2.0-flash")

def get_nutrition_insights(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    prompt = f"""As a nutrition expert, analyze this meal and provide detailed nutritional insights:

Food Analysis Data:
{json.dumps(analysis_data)}

Provide concise, actionable insights about:
1. Macronutrient Balance
2. Micronutrient Highlights
3. Health Benefits
4. Potential Concerns
5. Recommendations

Format the response as a JSON with these fields:
{{
    "macro_balance": {{
        "status": "good/needs_improvement",
        "details": "Brief analysis of protein/carbs/fat ratio",
        "recommendations": ["1-2 specific suggestions"]
    }},
    "micronutrients": {{
        "highlights": ["Key vitamins/minerals present"],
        "deficiencies": ["Notable missing nutrients"]
    }},
    "health_benefits": ["3-4 specific benefits"],
    "concerns": ["1-2 potential issues to watch"],
    "recommendations": ["2-3 actionable suggestions"]
}}

Keep insights precise, evidence-based, and directly related to the analyzed food items."""
    
    try:
        response = gemini_model.generate_content(prompt)
        result = clean_json_response(response.text)
        
        # Validate the result structure
        if result and isinstance(result, dict):
            # Ensure all required fields exist
            validated_result = {
                "macro_balance": result.get("macro_balance", {"status": "unknown", "details": "Analysis failed", "recommendations": []}),
                "micronutrients": result.get("micronutrients", {"highlights": [], "deficiencies": []}),
                "health_benefits": result.get("health_benefits", []),
                "concerns": result.get("concerns", []),
                "recommendations": result.get("recommendations", ["Unable to analyze nutrition data"])
            }
            
            # Validate macro_balance structure
            if not isinstance(validated_result["macro_balance"], dict):
                validated_result["macro_balance"] = {"status": "unknown", "details": "Analysis failed", "recommendations": []}
            else:
                macro_balance = validated_result["macro_balance"]
                if "status" not in macro_balance:
                    macro_balance["status"] = "unknown"
                if "details" not in macro_balance:
                    macro_balance["details"] = "Analysis completed"
                if "recommendations" not in macro_balance:
                    macro_balance["recommendations"] = []
            
            return validated_result
        else:
            return {
                "macro_balance": {"status": "unknown", "details": "Analysis failed", "recommendations": []},
                "micronutrients": {"highlights": [], "deficiencies": []},
                "health_benefits": [],
                "concerns": [],
                "recommendations": ["Unable to analyze nutrition data"]
            }
    except Exception as e:
        print(f"Nutrition insights error: {e}")
        return {
            "macro_balance": {"status": "error", "details": f"Analysis failed: {str(e)}", "recommendations": []},
            "micronutrients": {"highlights": [], "deficiencies": []},
            "health_benefits": [],
            "concerns": ["Service temporarily unavailable"],
            "recommendations": ["Please try again later"]
        }