import sys
import asyncio
from dotenv import load_dotenv

# Load env before importing anything else
load_dotenv()

from src.graph.workflow import app

def run_mission(query: str):
    print("="*60)
    print(f"🚀 INITIALIZING DEEP RESEARCH MISSION")
    print(f"🎯 TARGET: {query}")
    print("="*60)

    initial_state = {
        "user_query": query,
        "plan": [],
        "findings": [],
        "current_step_index": 0
    }

    # Execute the Graph
    # We use .invoke for synchronous execution in CLI
    final_state = app.invoke(initial_state)

    print("\n" + "="*60)
    print("✅ MISSION COMPLETE. FINAL REPORT:")
    print("="*60 + "\n")
    print(final_state["final_answer"])
    print("\n" + "="*60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        user_query = input("Enter Research Query: ")
    
    run_mission(user_query)