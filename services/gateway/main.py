from fastapi import FastAPI, HTTPException
import httpx
import os

app = FastAPI(title="DevAgents - API Gateway")

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:8001")

@app.get("/")
def read_root():
    return {"service": "API Gateway", "status": "online"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/task")
async def handle_task(payload: dict):
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            response = await client.post(f"{ORCHESTRATOR_URL}/orchestrate", json=payload)
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Orchestrator service unavailable: {exc}")