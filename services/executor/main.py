import subprocess
import sys
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="DevAgents - Executor Service")

class ExecutionRequest(BaseModel):
    code: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/run")
def run_code(request: ExecutionRequest):
    try:
        # Ejecución aislada en subproceso con tiempo límite (10s)
        result = subprocess.run(
            [sys.executable, "-c", request.code],
            capture_output=True,
            text=True,
            timeout=10
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": "Execution timed out (10s threshold reached)."
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e)
        }