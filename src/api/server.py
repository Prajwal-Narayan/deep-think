from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
from src.graph.workflow import app as graph_app

# Initialize FastAPI
app = FastAPI(title="Deep Research API", version="1.0")

# Allow CORS (So our React UI can talk to this)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, lock this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    query: str

async def event_generator(query: str):
    """
    Generator function that streams graph events to the client.
    """
    initial_state = {
        "user_query": query,
        "plan": [],
        "findings": [],
        "current_step_index": 0
    }

    # Stream events from LangGraph
    # We use .astream to get async updates
    async for event in graph_app.astream(initial_state):
        
        # 1. Handle Chain Updates (Plan generation, Step execution)
        for node_name, node_state in event.items():
            
            # Prepare a clean update payload
            update = {
                "type": "update",
                "node": node_name,
                "data": {}
            }

            if node_name == "planner":
                update["data"] = {"plan": node_state.get("plan")}
            
            elif node_name == "executor":
                # Find the finding we just added
                if "findings" in node_state and node_state["findings"]:
                    latest_finding = node_state["findings"][-1]
                    update["data"] = {"log": f"Step executed. Found data."} 
            
            elif node_name == "reporter":
                 update["data"] = {"final_answer": node_state.get("final_answer")}
            
            # Send JSON string as an SSE event
            yield f"data: {json.dumps(update)}\n\n"

    # Send Done Signal
    yield "data: [DONE]\n\n"

@app.post("/research")
async def start_research(request: ResearchRequest):
    """
    Endpoint to start the Deep Research agent.
    Returns a StreamingResponse.
    """
    return StreamingResponse(event_generator(request.query), media_type="text/event-stream")

@app.get("/health")
def health_check():
    return {"status": "operational", "system": "Deep Research v1"}

# --- RUNNER ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)