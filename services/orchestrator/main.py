import sys
import os
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from graph import app_graph

try:
    from langfuse.langchain import CallbackHandler
except ImportError:
    from langfuse.callback import CallbackHandler

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from memory.db import save_task_memory, get_recent_history


from db import init_postgres, save_task_metrics_pg, save_full_trace_mongo, redis_client

app = FastAPI(title="DevAgents - Orchestrator Service")


@app.on_event("startup")
def startup_event():
    init_postgres()

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
    task_id = str(uuid.uuid4())


    cache_key = f"task_cache:{hash(request.task)}"
    cached_result = redis_client.get(cache_key)
    if cached_result:
        print(f"[Redis Cache Hit] Returning result from cache for the task")


    history = get_recent_history(limit=2)
    memory_context = ""
    approved_tasks = [h for h in history if h.get("is_approved")]
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
        print(f"[Memory Warning] Could not be saved in memory: {e}")


    save_task_metrics_pg(
        task_id=task_id,
        status="completed",
        iterations=final_state.get("iterations", 0),
        is_approved=final_state.get("is_approved", False)
    )
    save_full_trace_mongo(task_id=task_id, final_state=final_state)

    return {
        "task_id": task_id,
        "status": "completed",
        "iterations": final_state.get("iterations", 0),
        "is_approved": final_state.get("is_approved", False),
        "plan": final_state.get("plan", ""),
        "code": final_state.get("code", ""),
        "review": final_state.get("review", "")
    }