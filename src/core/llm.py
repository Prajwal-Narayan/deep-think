from litellm import completion
from src.core.config import get_settings

settings = get_settings()

def call_brain(messages: list, temperature: float = 0.7, json_mode: bool = False) -> str:
    """
    Routes complex reasoning tasks to the 'Brain' model (Gemini 1.5 Pro).
    Args:
        messages: List of {"role": "user", "content": "..."}
        temperature: Creativity (0.7 for planning, 0.2 for logic)
        json_mode: If True, forces valid JSON output (Crucial for Planner)
    """
    response_format = {"type": "json_object"} if json_mode else None
    
    try:
        response = completion(
            model=settings.MODEL_BRAIN,
            messages=messages,
            temperature=temperature,
            api_key=settings.GEMINI_API_KEY,
            response_format=response_format
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ [BRAIN FAILURE]: {e}")
        raise e

def call_muscle(messages: list, temperature: float = 0.2) -> str:
    """
    Routes heavy-lifting tasks to the 'Muscle' model (Gemini 1.5 Flash).
    Used for reading long context or simple extraction.
    """
    try:
        response = completion(
            model=settings.MODEL_MUSCLE,
            messages=messages,
            temperature=temperature,
            api_key=settings.GEMINI_API_KEY
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ [MUSCLE FAILURE]: {e}")
        raise e

# --- SMOKE TEST (Run this file directly) ---
if __name__ == "__main__":
    print("Testing Neural Pathways...")
    
    # Test Brain
    print("\n🧠 PING BRAIN (Pro):")
    brain_reply = call_brain([{"role": "user", "content": "Explain 'Deep Reasoning' in one sentence."}])
    print(f"Output: {brain_reply}")
    
    # Test Muscle
    print("\n💪 PING MUSCLE (Flash):")
    muscle_reply = call_muscle([{"role": "user", "content": "Repeat the word 'Work' 5 times."}])
    print(f"Output: {muscle_reply}")