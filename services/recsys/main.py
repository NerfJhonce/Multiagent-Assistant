import os
from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient

app = FastAPI(title="DevAgents - Recommendation System (RecSys)")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongodb:27017/devagents_nosql")
mongo_client = MongoClient(MONGO_URL)
mongo_db = mongo_client["devagents_nosql"]
agent_logs = mongo_db["agent_execution_logs"]


class RecommendationRequest(BaseModel):
    task: str


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "RecSys"}


@app.post("/recommend")
def recommend_next_steps(request: RecommendationRequest):

    recent_traces = list(agent_logs.find().limit(5))

    recommendations = [
        "Add automated unit tests (pytest) to the generated code",
        "Optimize time complexity in detected loops",
        "Document functions with docstrings in Google Style format"
    ]

    return {
        "input_task": request.task,
        "recommendations": recommendations,
        "historical_context_count": len(recent_traces)
    }