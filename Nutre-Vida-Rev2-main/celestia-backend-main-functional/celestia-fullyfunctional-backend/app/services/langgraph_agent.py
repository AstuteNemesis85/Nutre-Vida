"""
LangGraph-based Health Coach Agent
Replaces direct Gemini calls with a structured graph:
  analyze_intent → retrieve_context (RAG) → generate_response (LLM + tools) → format_output
"""

import json
from datetime import datetime, timedelta
from typing import Any, Annotated, Dict, List, Optional, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.config import settings
from app.services.rag_service import get_rag_service

# ---------------------------------------------------------------------------
# Agent State
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    """State flowing through the LangGraph graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_id: int
    session_id: str
    user_profile: Dict[str, Any]
    user_meal_history: Dict[str, Any]
    retrieved_context: str
    health_alerts: List[Dict[str, Any]]
    intent: str
    final_response: str


# ---------------------------------------------------------------------------
# Tools  (decorated functions callable by the LLM)
# ---------------------------------------------------------------------------

@tool
def search_nutrition_kb(query: str) -> str:
    """Search the nutrition knowledge base for information about Indian foods, dietary guidelines, health conditions, and Ayurvedic principles."""
    rag = get_rag_service()
    results = rag.retrieve_nutrition_knowledge(query, top_k=3)
    if not results:
        return "No specific nutrition knowledge found for this query."
    parts = []
    for r in results:
        parts.append(f"[{r['metadata'].get('title', 'Info')}] {r['content'][:500]}")
    return "\n---\n".join(parts)


@tool
def search_user_meals(user_id: int, query: str) -> str:
    """Search a user's past meal history for specific foods, nutrition data, or eating patterns."""
    rag = get_rag_service()
    results = rag.retrieve_user_meals(user_id, query, top_k=5)
    if not results:
        return "No matching meals found in user's history."
    parts = []
    for r in results:
        parts.append(r["content"])
    return "\n".join(parts)


@tool
def get_daily_nutrition_summary(meal_history: str) -> str:
    """Summarise the user's recent daily nutrition from their meal history data (provided as text). Returns a concise summary of calories, protein, carbs, fat averages."""
    # The LLM can call this to explicitly request a summary view
    return f"User's recent meal history for analysis:\n{meal_history[:2000]}"


@tool
def calculate_nutrition_gap(current_intake: str, daily_goals: str) -> str:
    """Calculate the gap between current nutritional intake and daily goals. Both inputs are JSON strings with keys like calories, protein, carbs, fat."""
    try:
        intake = json.loads(current_intake) if isinstance(current_intake, str) else current_intake
        goals = json.loads(daily_goals) if isinstance(daily_goals, str) else daily_goals
        gaps = {}
        for key in ["calories", "protein", "carbs", "fat"]:
            goal_val = float(goals.get(key, 0))
            curr_val = float(intake.get(key, 0))
            if goal_val > 0:
                gaps[key] = {
                    "goal": goal_val,
                    "current": curr_val,
                    "remaining": round(goal_val - curr_val, 1),
                    "percent_achieved": round((curr_val / goal_val) * 100, 1),
                }
        return json.dumps(gaps, indent=2)
    except Exception as e:
        return f"Error calculating gaps: {e}"


# All tools the agent can invoke
ALL_TOOLS = [
    search_nutrition_kb,
    search_user_meals,
    get_daily_nutrition_summary,
    calculate_nutrition_gap,
]


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

def _get_llm(with_tools: bool = True) -> ChatGoogleGenerativeAI:
    """Get the ChatGoogleGenerativeAI LLM instance bound to tools."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.google_api_key,
        temperature=0.7,
        max_output_tokens=2048,
    )
    if with_tools:
        return llm.bind_tools(ALL_TOOLS)
    return llm


SYSTEM_PROMPT = """You are **NutreVida AI Health Coach**, an expert in Indian nutrition and wellness.

PERSONALITY:
- Warm, encouraging friend who knows nutrition deeply
- Concise: 2-3 sentences for simple queries, 4-5 for complex ones
- Use the user's actual meal data and profile — never give generic advice
- Reference specific foods, calorie/macro numbers from their history
- Understand Indian food culture, regional dishes, Ayurvedic principles
- Celebrate small wins, never preachy or judgmental

TOOLS:
- Use `search_nutrition_kb` when you need factual nutrition information (e.g., protein in paneer, GI of rice)
- Use `search_user_meals` when you need to look up the user's specific past meals
- Use `calculate_nutrition_gap` when comparing intake vs goals
- You may decide NOT to use any tool if the context already provides enough information

RESPONSE RULES:
1. Reference their REAL meals and numbers when relevant
2. Give ONE key actionable suggestion
3. End with encouragement
4. Use max 1-2 emojis
5. For meal history questions, present data in a clean, readable format
"""


# ---------------------------------------------------------------------------
# Graph Nodes
# ---------------------------------------------------------------------------

def analyze_intent(state: AgentState) -> dict:
    """Classify the user's intent so we can route appropriately."""
    last_msg = ""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            last_msg = m.content
            break

    msg_lower = last_msg.lower()

    # Simple keyword-based intent detection
    if any(kw in msg_lower for kw in ["meal plan", "plan my meals", "weekly plan", "diet plan"]):
        intent = "meal_planning"
    elif any(kw in msg_lower for kw in [
        "what did i eat", "my meals", "food history", "yesterday", "past meals",
        "calories consumed", "my diet", "eating pattern"
    ]):
        intent = "meal_history"
    elif any(kw in msg_lower for kw in [
        "nutrient", "vitamin", "mineral", "iron", "calcium", "protein info",
        "glycemic", "gi of", "carbs in", "calories in", "how much protein"
    ]):
        intent = "nutrition_lookup"
    elif any(kw in msg_lower for kw in [
        "goal", "target", "progress", "how am i doing", "on track"
    ]):
        intent = "goal_tracking"
    else:
        intent = "general_chat"

    return {"intent": intent}


def retrieve_context(state: AgentState) -> dict:
    """Use RAG to pull in relevant context before the LLM generates a response."""
    rag = get_rag_service()
    last_msg = ""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            last_msg = m.content
            break

    user_id = state.get("user_id", 0)
    intent = state.get("intent", "general_chat")
    context_parts: List[str] = []

    # Always retrieve nutrition knowledge for nutrition-related intents
    if intent in ("nutrition_lookup", "general_chat", "meal_planning", "goal_tracking"):
        nutrition_docs = rag.retrieve_nutrition_knowledge(last_msg, top_k=3)
        if nutrition_docs:
            context_parts.append("NUTRITION KNOWLEDGE:")
            for doc in nutrition_docs:
                score = doc.get("relevance_score", 0)
                if score > 0.3:  # Only include sufficiently relevant docs
                    context_parts.append(f"- {doc['content'][:400]}")

    # Retrieve relevant past meals
    if intent in ("meal_history", "goal_tracking", "general_chat"):
        meal_docs = rag.retrieve_user_meals(user_id, last_msg, top_k=5)
        if meal_docs:
            context_parts.append("\nRELEVANT PAST MEALS:")
            for doc in meal_docs:
                context_parts.append(f"- {doc['content']}")

    # Retrieve relevant past conversations
    convo_docs = rag.retrieve_conversation_context(user_id, last_msg, top_k=3)
    if convo_docs:
        context_parts.append("\nRELEVANT PAST CONVERSATIONS:")
        for doc in convo_docs:
            score = doc.get("relevance_score", 0)
            if score > 0.3:
                context_parts.append(f"- {doc['content'][:200]}")

    retrieved_text = "\n".join(context_parts) if context_parts else "No additional context retrieved."
    return {"retrieved_context": retrieved_text}


def build_prompt_and_call_llm(state: AgentState) -> dict:
    """Build the full prompt with all context, then call the LLM (possibly with tool calls)."""
    user_profile = state.get("user_profile", {})
    meal_history = state.get("user_meal_history", {})
    retrieved_context = state.get("retrieved_context", "")
    health_alerts = state.get("health_alerts", [])

    # Format user profile
    profile_lines = []
    if user_profile:
        profile_lines.append(f"Name: {user_profile.get('name', 'User')}")
        goals = user_profile.get("daily_goals", {})
        if goals:
            profile_lines.append(f"Daily Goals: {json.dumps(goals)}")
        prefs = user_profile.get("profile", {})
        if prefs.get("health_goals"):
            profile_lines.append(f"Health Goals: {', '.join(prefs['health_goals'])}")
        if prefs.get("dietary_preferences"):
            profile_lines.append(f"Diet: {', '.join(prefs['dietary_preferences'])}")
        if prefs.get("allergies"):
            profile_lines.append(f"Allergies: {', '.join(prefs['allergies'])}")

    # Format meal history summary
    meal_lines = []
    recent_meals = meal_history.get("recent_meals", [])[:10]
    for meal in recent_meals:
        nutrition = meal.get("nutrition_summary", {})
        foods = []
        for item in meal.get("analysis_data", {}).get("items", []):
            n = item.get("name") or item.get("food_name") or "food"
            foods.append(n)
        cal = nutrition.get("total_calories", "?")
        prot = nutrition.get("total_protein", "?")
        meal_lines.append(
            f"- {meal.get('upload_date', '?')} ({meal.get('meal_type', 'meal')}): "
            f"{', '.join(foods[:3]) if foods else 'items'} — {cal} cal, {prot}g protein"
        )

    # Format health alerts
    alert_lines = []
    for a in health_alerts[:3]:
        alert_lines.append(f"⚠️ [{a.get('severity', 'info')}] {a.get('message', a.get('alert_type', ''))}")

    # Build the context block that goes into the system message
    context_block = f"""
USER PROFILE:
{chr(10).join(profile_lines) if profile_lines else 'Not available'}

RECENT MEAL HISTORY:
{chr(10).join(meal_lines) if meal_lines else 'No meals logged yet'}

HEALTH ALERTS:
{chr(10).join(alert_lines) if alert_lines else 'No active alerts'}

RAG RETRIEVED CONTEXT:
{retrieved_context}
"""

    full_system = SYSTEM_PROMPT + "\n\n---\nCONTEXT FOR THIS CONVERSATION:\n" + context_block

    # Rebuild messages: system + conversation history
    new_messages = [SystemMessage(content=full_system)]
    for m in state["messages"]:
        if not isinstance(m, SystemMessage):
            new_messages.append(m)

    llm = _get_llm(with_tools=True)
    response = llm.invoke(new_messages)

    return {"messages": [response]}


def format_output(state: AgentState) -> dict:
    """Extract the final text response from the last AI message."""
    for m in reversed(state["messages"]):
        if isinstance(m, AIMessage) and m.content:
            content = m.content
            # Handle cases where content is a list of content blocks
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, str):
                        text_parts.append(block)
                    elif isinstance(block, dict) and block.get("text"):
                        text_parts.append(block["text"])
                content = "\n".join(text_parts) if text_parts else str(content)
            return {"final_response": content}
    return {"final_response": "I'm here to help! Could you tell me more about what you'd like to know?"}


# ---------------------------------------------------------------------------
# Conditional edge: should we call tools or go straight to output?
# ---------------------------------------------------------------------------

def should_use_tools(state: AgentState) -> str:
    """Check if the last AI message contains tool calls."""
    for m in reversed(state["messages"]):
        if isinstance(m, AIMessage):
            if hasattr(m, "tool_calls") and m.tool_calls:
                return "tools"
            break
    return "output"


# ---------------------------------------------------------------------------
# Build the Graph
# ---------------------------------------------------------------------------

def build_health_coach_graph() -> StateGraph:
    """Construct and compile the LangGraph health coach agent."""

    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("analyze_intent", analyze_intent)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("generate", build_prompt_and_call_llm)
    graph.add_node("tools", ToolNode(ALL_TOOLS))
    graph.add_node("format_output", format_output)

    # Edges
    graph.set_entry_point("analyze_intent")
    graph.add_edge("analyze_intent", "retrieve_context")
    graph.add_edge("retrieve_context", "generate")

    # After generate: either call tools or go to output
    graph.add_conditional_edges(
        "generate",
        should_use_tools,
        {"tools": "tools", "output": "format_output"},
    )

    # After tools, loop back to generate so the LLM can see tool results
    graph.add_edge("tools", "generate")

    # format_output → END
    graph.add_edge("format_output", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Module-level compiled graph (singleton)
# ---------------------------------------------------------------------------

_compiled_graph = None


def get_health_coach_graph():
    """Get or create the compiled LangGraph health coach graph."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_health_coach_graph()
    return _compiled_graph


# ---------------------------------------------------------------------------
# High-level invocation helper
# ---------------------------------------------------------------------------

async def run_health_coach(
    user_id: int,
    message: str,
    session_id: str,
    user_profile: Dict[str, Any] = None,
    user_meal_history: Dict[str, Any] = None,
    health_alerts: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run the LangGraph health coach agent and return the response.
    This is the main entry point called by EnhancedAgenticService.
    """
    graph = get_health_coach_graph()

    initial_state: AgentState = {
        "messages": [HumanMessage(content=message)],
        "user_id": user_id,
        "session_id": session_id,
        "user_profile": user_profile or {},
        "user_meal_history": user_meal_history or {},
        "retrieved_context": "",
        "health_alerts": health_alerts or [],
        "intent": "",
        "final_response": "",
    }

    # Invoke the graph
    try:
        result = await graph.ainvoke(initial_state)
        final_text = result.get("final_response", "")
        intent = result.get("intent", "general_chat")

        # Also index this conversation in RAG for future retrieval
        rag = get_rag_service()
        rag.index_conversation(user_id, session_id, "user", message)
        rag.index_conversation(user_id, session_id, "assistant", final_text)

        return {
            "message": final_text,
            "intent": intent,
            "response_type": intent,
            "confidence": 0.9,
            "actions": _extract_actions(final_text, intent),
            "trigger_notifications": intent == "meal_planning",
        }
    except Exception as e:
        print(f"[LangGraph] Error running health coach: {e}")
        import traceback
        traceback.print_exc()
        return {
            "message": "I'm having a moment — could you try asking again?",
            "intent": "error",
            "response_type": "error",
            "confidence": 0.3,
            "actions": [],
            "trigger_notifications": False,
            "error": str(e),
        }


def _extract_actions(text, intent: str) -> List[str]:
    """Extract suggested actions from the response text and intent."""
    actions = []
    if not isinstance(text, str):
        text = str(text)
    text_lower = text.lower()
    if "try" in text_lower or "consider" in text_lower:
        actions.append("dietary_adjustment")
    if "track" in text_lower or "log" in text_lower:
        actions.append("meal_tracking")
    if "plan" in text_lower:
        actions.append("meal_planning")
    if intent == "goal_tracking":
        actions.append("review_goals")
    return actions


# ---------------------------------------------------------------------------
# Meal Plan Sub-Graph
# ---------------------------------------------------------------------------

async def generate_langgraph_meal_plan(
    user_id: int,
    user_profile: Dict[str, Any],
    preferences: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a meal plan using a dedicated LangGraph sub-graph flow."""
    llm = _get_llm(with_tools=False)
    rag = get_rag_service()

    # Retrieve relevant nutrition context for meal planning
    goals = preferences.get("goals", {})
    dietary = goals.get("dietary_restrictions", "none")
    cuisine = goals.get("cuisine_preference", "Indian")
    duration = preferences.get("duration_days", 7)

    query = f"meal planning {dietary} {cuisine} balanced nutrition daily meals"
    nutrition_context = rag.retrieve_nutrition_knowledge(query, top_k=5)
    context_text = "\n".join(
        [doc["content"][:400] for doc in nutrition_context]
    ) if nutrition_context else "Use general Indian nutrition knowledge."

    profile_data = user_profile.get("profile", {})
    daily_goals = user_profile.get("daily_goals", {})

    prompt = f"""You are a nutrition expert. Generate a {duration}-day meal plan.

User Profile: {json.dumps(profile_data)}
Daily Goals: {json.dumps(daily_goals)}
Preferences: {json.dumps(goals)}

NUTRITION KNOWLEDGE (use this to make the plan accurate):
{context_text}

Return a JSON object with this EXACT structure:
{{
  "days": [
    {{
      "day": "Day 1",
      "meals": {{
        "breakfast": [{{"name": "food item with quantity", "calories": 300}}],
        "lunch": [{{"name": "food item with quantity", "calories": 500}}],
        "dinner": [{{"name": "food item with quantity", "calories": 400}}],
        "snack": [{{"name": "food item with quantity", "calories": 150}}]
      }}
    }}
  ]
}}

IMPORTANT:
- Include Indian cuisine where appropriate
- Match dietary restrictions: {dietary}
- Target ~{goals.get('calorie_target', 2000)} calories/day
- Cuisine preference: {cuisine}
- Include 2-3 food items per meal for variety
- Return ONLY valid JSON, no markdown or extra text"""

    import re
    import time

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            response_text = response.content

            # Parse JSON
            response_text = re.sub(r"```json\s*", "", response_text)
            response_text = re.sub(r"```\s*", "", response_text)
            response_text = response_text.strip()
            plan_data = json.loads(response_text)

            return {
                "meal_plan": plan_data,
                "plan_type": preferences.get("plan_type", "weekly"),
                "duration_days": duration,
                "generation_method": "langgraph_rag",
            }
        except Exception as api_error:
            if "429" in str(api_error) and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 30
                print(f"[LangGraph] Rate limited on meal plan, waiting {wait_time}s (attempt {attempt + 1})")
                time.sleep(wait_time)
            elif attempt == max_retries - 1:
                print(f"[LangGraph] Meal plan generation failed: {api_error}")
                return {"error": f"Failed to generate meal plan: {str(api_error)}"}
            else:
                raise
    return {"error": "Failed to generate meal plan after retries"}
