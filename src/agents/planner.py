import json
from src.core.llm import call_brain
from src.core.state import ResearchPlan

# The Directive (System Prompt)
# UPDATED: Added explicit JSON Example to prevent schema mismatch
PLANNER_PROMPT = """
You are a Senior Research Architect.
Your goal is to break down a complex user query into a step-by-step research plan.

**Available Tools:**
1. `web_search`: For current events, news, competitors, market data (Post-2023).
2. `document_search`: For looking up specific details in uploaded files (e.g., 10-K, Manuals).
3. `synthesis`: The final step to combine findings into an answer.

**Rules:**
- Keep the plan efficient (Max 4-5 steps).
- Steps must be sequential.
- If the query is simple, use fewer steps.
- RETURN ONLY VALID JSON.

**JSON Format Output:**
{
  "steps": [
    {
      "id": 1,
      "title": "Search Competitor Strategy",
      "query": "AMD AI chip strategy 2024",
      "tool": "web_search",
      "reasoning": "Need to find recent news on competitor products."
    }
  ]
}
"""

def generate_plan(user_query: str) -> dict:
    """
    Invokes the 'Brain' model to create a research plan.
    """
    print(f"🧠 [Brain] Generating plan for: {user_query}")
    
    messages = [
        {"role": "system", "content": PLANNER_PROMPT},
        {"role": "user", "content": f"User Query: {user_query}"}
    ]
    
    # 1. Call Brain (Disable json_mode for stability on new models, trust the prompt)
    raw_response = call_brain(messages, json_mode=False)
    
    # 2. Parse & Validate
    try:
        # Clean potential markdown wrappers
        clean_json = raw_response.replace("```json", "").replace("```", "").strip()
        plan_data = json.loads(clean_json)
        
        # ROBUSNESS FIX: Handle cases where LLM wraps response in a 'plan' key
        if "plan" in plan_data and "steps" not in plan_data:
            plan_data = {"steps": plan_data["plan"]}
        
        # Validate structure with Pydantic
        validated_plan = ResearchPlan(**plan_data)
        
        # Return partial state update
        return {
            "plan": [step.model_dump() for step in validated_plan.steps], 
            "current_step_index": 0,
            "findings": []
        }
        
    except Exception as e:
        print(f"❌ [Brain Error] Failed to parse plan: {e}")
        print(f"DEBUG: Raw Response from LLM: {raw_response}") 
        
        # Emergency Fallback
        return {
            "plan": [{
                "id": 1, 
                "title": "Fallback Search", 
                "query": user_query, 
                "tool": "web_search",
                "reasoning": "Planner failed, defaulting to basic search."
            }], 
            "current_step_index": 0,
            "findings": []
        }

# --- SMOKE TEST ---
if __name__ == "__main__":
    query = "Analyze the competitive risks of NVIDIA vs AMD in 2024"
    result = generate_plan(query)
    print("\n✅ GENERATED PLAN:")
    print(json.dumps(result, indent=2))