from langgraph.graph import StateGraph, END
from src.core.state import AgentState
from src.agents.planner import generate_plan
from src.tools.search import perform_web_search, perform_document_search
from src.core.llm import call_brain

# --- 1. NODES ( The Agents ) ---

def plan_node(state: AgentState):
    """
    The Architect.
    Analyzes the query and generates a step-by-step JSON plan.
    """
    print(f"\n🧠 [PLANNING] Analyzing: {state['user_query']}")
    plan_result = generate_plan(state['user_query'])
    # Update state with the new plan
    return plan_result

def execute_step_node(state: AgentState):
    """
    The Worker.
    Executes the current step in the plan using the correct tool.
    """
    plan = state["plan"]
    current_idx = state["current_step_index"]
    
    # Safety Check
    if current_idx >= len(plan):
        return {"findings": []}

    current_step = plan[current_idx]
    print(f"⚡ [EXECUTION] Step {current_step['id']}: {current_step['title']}")
    print(f"   Tool: {current_step['tool']} | Query: {current_step['query']}")

    # ROUTING LOGIC
    result = ""
    if current_step["tool"] == "web_search":
        result = perform_web_search(current_step["query"])
    elif current_step["tool"] == "document_search":
        result = perform_document_search(current_step["query"])
    elif current_step["tool"] == "synthesis":
        result = "Synthesis step reached. Proceeding to final answer."
    else:
        result = f"Unknown tool: {current_step['tool']}"

    # Format the finding
    finding_str = f"Step {current_step['id']} ({current_step['title']}):\n{result}\n"
    
    # Return update (operator.add will append this to the list)
    return {"findings": [finding_str]}

def reflection_node(state: AgentState):
    """
    The Manager.
    Just increments the step index. 
    (In v2, this is where we'd add 'Self-Correction' logic)
    """
    return {"current_step_index": state["current_step_index"] + 1}

def synthesis_node(state: AgentState):
    """
    The Editor.
    Compiles all findings into a final "God Tier" report.
    """
    print("📝 [SYNTHESIS] Compiling Final Report...")
    
    findings_text = "\n".join(state["findings"])
    plan_text = "\n".join([f"- {s['title']}" for s in state["plan"]])
    
    system_prompt = """
    You are a Senior Research Analyst.
    Write a comprehensive, professional research report based on the provided findings.
    
    Structure:
    1. Executive Summary
    2. Key Findings (Cite sources using [Source: URL/Doc])
    3. Strategic Analysis (Connect the dots)
    4. Conclusion
    
    Tone: Professional, Objective, Data-Driven.
    """
    
    user_prompt = f"""
    Original Query: {state['user_query']}
    
    Research Plan Executed:
    {plan_text}
    
    Raw Findings:
    {findings_text}
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    final_report = call_brain(messages)
    return {"final_answer": final_report}

# --- 2. EDGES ( The Logic Flow ) ---

def should_continue(state: AgentState):
    """
    Decides if we loop back to execution or finish.
    """
    if state["current_step_index"] < len(state["plan"]):
        return "continue"
    else:
        return "end"

# --- 3. GRAPH ASSEMBLY ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("planner", plan_node)
workflow.add_node("executor", execute_step_node)
workflow.add_node("reflector", reflection_node)
workflow.add_node("reporter", synthesis_node)

# Set Entry Point
workflow.set_entry_point("planner")

# Add Edges
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "reflector")

# Conditional Edge (Loop or Finish)
workflow.add_conditional_edges(
    "reflector",
    should_continue,
    {
        "continue": "executor",
        "end": "reporter"
    }
)

workflow.add_edge("reporter", END)

# Compile
app = workflow.compile()