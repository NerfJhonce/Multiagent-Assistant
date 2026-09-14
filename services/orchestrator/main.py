import sys
import os
from fastapi import FastAPI
from pydantic import BaseModel
from graph import app_graph

try:
    from langfuse.langchain import CallbackHandler
except ImportError:
    from langfuse.callback import CallbackHandler

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from memory.db import save_task_memory, get_recent_history

app = FastAPI(title="DevAgents - Orchestrator Service")

class TaskRequest(BaseModel):
    task: str

@app.get("/")
def read_root():
    return {"service": "Orchestrator", "status": "online"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/orchestrate")
async def orchestrate_task(request: TaskRequest):
    langfuse_handler = CallbackHandler()

    # Recuperar el historial reciente de tareas aprobadas
    history = get_recent_history(limit=2)
    memory_context = ""
    approved_tasks = [h for h in history if h["is_approved"]]
    if approved_tasks:
        memory_context = "\n".join([f"- Prior Task: {h['task']}\n  Code Reference: {h['code']}" for h in approved_tasks])

    task_prompt = request.task
    if memory_context:
        task_prompt += f"\n\n[Relevant Memory Context]\n{memory_context}"

    initial_state = {
        "task": task_prompt,
        "plan": "",
        "research": "",
        "code": "",
        "review": "",
        "test_output": "",
        "is_approved": False,
        "iterations": 0
    }

    final_state = await app_graph.ainvoke(
        initial_state,
        config={"callbacks": [langfuse_handler]}
    )

    try:
        save_task_memory(
            task=request.task,
            plan=final_state.get("plan", ""),
            code=final_state.get("code", ""),
            is_approved=final_state.get("is_approved", False)
        )
    except Exception as e:
        print(f"[Memory Warning] No se pudo guardar en memoria: {e}")

    return {
        "status": "completed",
        "iterations": final_state.get("iterations", 0),
        "is_approved": final_state.get("is_approved", False),
        "plan": final_state.get("plan", ""),
        "code": final_state.get("code", ""),
        "review": final_state.get("review", "")
    }