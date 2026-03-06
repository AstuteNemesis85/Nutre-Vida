import io
import json
import re
from typing import Any, Dict, List, Optional, Union

import google.generativeai as genai
from PIL import Image

from app.config import settings

genai.configure(api_key=settings.google_api_key)
gemini_model = genai.GenerativeModel("models/gemini-2.0-flash")

def clean_json_response(text: str) -> Optional[Dict[str, Any]]:
    text = re.sub(r'```json', '', text)
    text = re.sub(r'```', '', text)
    text = text.strip()
    brace_count = 0
    start_idx = -1
    end_idx = -1
    for i, char in enumerate(text):
        if char == '{':
            if start_idx == -1:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                end_idx = i + 1
                break
    if start_idx != -1 and end_idx != -1:
        json_text = text[start_idx:end_idx]
        try:
            return json.loads(json_text)
        except Exception as e:
            print(f"JSON parsing error: {e}")
            return None
    return None

def create_fallback_response(error_msg: str) -> Dict[str, Any]:
    return {
        "items": [],
        "total_calories": 0,
        "total_protein": 0,
        "total_carbs": 0,
        "total_fat": 0,
        "confidence_overall": 0,
        "need_clarification": True,
        "unclear_items": [f"Analysis failed: {error_msg}. Please try again."]
    }

def analyze_food_image(image_or_text: Union[Image.Image, str], user_profile: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Analyze food from image or text description"""
    if isinstance(image_or_text, str):
        if not image_or_text.strip():
            return create_fallback_response("Empty text provided")
        dietary_context = ""
        if user_profile and user_profile.get('diet_preference'):
            dietary_context = f"Note: User prefers {user_profile['diet_preference']} food. "
        prompt = f"""
        You are a food nutrition expert. Analyze the following food items and provide nutrition information.
        {dietary_context}
        Food items: {image_or_text}
        Provide response in this EXACT JSON format:
        {{
            "items": [
                {{
            # Updating the Gemini model name to the latest version
            # This change is necessary for improved performance and accuracy
            # Ensure that the new model is compatible with existing functionality
        gemini_model = genai.GenerativeModel("models/gemini-2.0-flash")
                    "quantity": "estimated quantity",
                    "confidence": 85,
                    "calories": 250,
                    "protein": 12,
                    "carbs": 30,
                    "fat": 8,
                    "is_vegetarian": true
                }}
            ],
            "total_calories": 250,
            "total_protein": 12,
            "total_carbs": 30,
            "total_fat": 8,
            "confidence_overall": 85,
            "need_clarification": false,
            "unclear_items": []
        }}
        """
    else:
        try:
            if image_or_text.mode != 'RGB':
                image_or_text = image_or_text.convert('RGB')
        except Exception as e:
            return create_fallback_response(f"Invalid image format: {str(e)}")
        dietary_context = ""
        if user_profile and user_profile.get('diet_preference'):
            dietary_context = f"Note: User prefers {user_profile['diet_preference']} food. Please identify if items are vegetarian/non-vegetarian. "
        prompt = f"""
        You are a food nutrition expert. Analyze this food image and provide detailed nutrition information.
        {dietary_context}
        Provide response in this EXACT JSON format:
        {{
            "items": [
                {{
                    "name": "Food item name",
                    "quantity": "estimated quantity",
                    "confidence": 85,
                    "calories": 250,
                    "protein": 12,
                    "carbs": 30,
                    "fat": 8,
                    "is_vegetarian": true
                }}
            ],
            "total_calories": 250,
            "total_protein": 12,
            "total_carbs": 30,
            "total_fat": 8,
            "confidence_overall": 85,
            "need_clarification": false,
            "unclear_items": []
        }}
        If you need clarification about specific items, set need_clarification to true and list questions in unclear_items.
        """
    try:
        if isinstance(image_or_text, str):
            response = gemini_model.generate_content([prompt])
        else:
            response = gemini_model.generate_content([prompt, image_or_text])
        result = clean_json_response(response.text)
        if not result:
            return create_fallback_response("JSON parsing failed")
        return result
    except Exception as e:
        print(f"Analysis error: {e}")
        return create_fallback_response(f"Analysis service error: {str(e)}")

def generate_clarifying_questions(analysis_data: Dict[str, Any]) -> List[str]:
    unclear_items = analysis_data.get('unclear_items', [])
    if not unclear_items:
        return ["Can you provide more details about the food items?"]
    questions = []
    for item in unclear_items[:3]:
        if not item.endswith('?'):
            item += '?'
        questions.append(item)
    return questions

def refine_analysis_with_answers(original_data: Dict[str, Any], questions: List[str], answers: List[str]) -> Optional[Dict[str, Any]]:
    qa_text = ""
    for q, a in zip(questions, answers):
        qa_text += f"Q: {q}\nA: {a}\n"
    prompt = f"""
    Update the food analysis based on user clarifications.
    Original analysis: {json.dumps(original_data, indent=2)}
    User clarifications:
    {qa_text}
    Provide updated analysis in this EXACT JSON format:
    {{
        "items": [
            {{
                "name": "Updated food name",
                "quantity": "corrected quantity",
                "confidence": 95,
                "calories": 280,
                "protein": 15,
                "carbs": 25,
                "fat": 10
            }}
        ],
        "total_calories": 280,
        "total_protein": 15,
        "total_carbs": 25,
        "total_fat": 10,
        "confidence_overall": 95,
        "need_clarification": false,
        "unclear_items": []
    }}
    """
    try:
        response = gemini_model.generate_content([prompt])
        result = clean_json_response(response.text)
        return result if result else original_data
    except Exception as e:
        print(f"Refinement error: {e}")
        return original_data

def portion_estimation(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    estimates = {}
    for item in analysis_data.get('items', []):
        estimates[item.get('name', 'unknown')] = {
            "grams": 100,
            "volume": "medium serving",
            "confidence": item.get('confidence', 50)
        }
    return estimates

def explainability(analysis_data: Dict[str, Any]) -> str:
    prompt = f"""
    Provide nutrition insights for this food analysis:
    {json.dumps(analysis_data, indent=2)}
    Create a detailed explanation with:
    ## Key Highlights
    ## Health Benefits
    ## Areas for Improvement
    ## Recommendations
    Make it informative and actionable.
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Unable to generate explanation: {str(e)}"
