import os
from typing import TypedDict
import httpx
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    task: str
    plan: str
    research: str
    code: str
    review: str
    test_output: str
    is_approved: bool
    iterations: int


llm = ChatOllama(
    model="qwen2.5-coder",
    base_url="http://ollama:11434",
    temperature=0.1
)


def load_file(path: str) -> str:
    try:

        full_path = os.path.join("/app", path)
        if not os.path.exists(full_path):

            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(base_dir, path)

        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""



SOUL_SECURITY = load_file("soul/security_guidelines.md")
SKILL_PYTHON = load_file("skills/python_development.md")

PLANNER_SYSTEM = load_file("agents/planner/prompt_v1.md")
RESEARCHER_SYSTEM = load_file("agents/researcher/prompt_v1.md")
DEVELOPER_SYSTEM = load_file("agents/developer/prompt_v1.md")
REVIEWER_SYSTEM = load_file("agents/reviewer/prompt_v1.md")


# 1. PLANNER NODE
def planner_node(state: AgentState):
    prompt = f"{PLANNER_SYSTEM}\n\nTask: {state['task']}"
    response = llm.invoke(prompt)
    return {
        "plan": str(response.content),
        "iterations": 0,
        "is_approved": False,
        "review": "",
        "test_output": ""
    }


# 2. RESEARCHER NODE
def researcher_node(state: AgentState):
    prompt = f"{RESEARCHER_SYSTEM}\n\nTask: {state['task']}\nPlan: {state['plan']}\nProvide a concise 1-sentence technical guidance or library recommendation."
    response = llm.invoke(prompt)
    return {"research": str(response.content)}


# 3. DEVELOPER NODE
def developer_node(state: AgentState):
    prompt = (
        f"{DEVELOPER_SYSTEM}\n\n"
        f"Security Principles:\n{SOUL_SECURITY}\n\n"
        f"Development Skills:\n{SKILL_PYTHON}\n\n"
        f"Task: {state['task']}\n"
        f"Plan: {state['plan']}\n"
        f"Research Context: {state.get('research', '')}\n"
    )
    if state.get("review") or state.get("test_output"):
        prompt += f"\nFix errors:\n{state.get('test_output')}"

    response = llm.invoke(prompt)
    return {
        "code": str(response.content),
        "iterations": state.get("iterations", 0) + 1
    }


# 4. TESTER NODE
def tester_node(state: AgentState):
    raw_code = state["code"]
    if "```python" in raw_code:
        raw_code = raw_code.split("```python")[1].split("```")[0].strip()
    else:
        raw_code = raw_code.replace("```", "").strip()

    try:
        response = httpx.post(
            "http://executor:8002/run",
            json={"code": raw_code},
            timeout=10.0
        )
        data = response.json()
        return {
            "test_output": f"Exit Code: {data.get('exit_code')}\nSTDOUT: {data.get('stdout')}\nSTDERR: {data.get('stderr')}"
        }
    except Exception as e:
        return {"test_output": f"Execution failed: {str(e)}"}


# 5. REVIEWER NODE
def reviewer_node(state: AgentState):
    test_out = state.get("test_output", "")
    if "Exit Code: 0" in test_out and state.get("code"):
        return {"review": "APPROVED", "is_approved": True}

    prompt = f"{REVIEWER_SYSTEM}\n\nCode failed or printed errors.\nOutput:\n{test_out}"
    response = llm.invoke(prompt)
    return {"review": str(response.content), "is_approved": False}


def should_continue(state: AgentState):
    if state.get("is_approved") or state.get("iterations", 0) >= 2:
        return END
    return "developer"


workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("developer", developer_node)
workflow.add_node("tester", tester_node)
workflow.add_node("reviewer", reviewer_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "researcher")
workflow.add_edge("researcher", "developer")
workflow.add_edge("developer", "tester")
workflow.add_edge("tester", "reviewer")
workflow.add_conditional_edges("reviewer", should_continue)

app_graph = workflow.compile()