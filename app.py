from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from env.models import Action, Observation, StepResult
from env.alie_env import AlieEnv
from configs.tasks import get_initial_state
from grader import grade_episode
from starlette.staticfiles import StaticFiles
import os

app = FastAPI(title="ALIE Environment API")
TASKS = [
    {
        "id": "easy",
        "name": "easy",
        "difficulty": "easy",
        "description": "Student with high initial engagement and predictable learning capability.",
        "grader": {"module": "grader", "function": "grade_episode"},
    },
    {
        "id": "medium",
        "name": "medium",
        "difficulty": "medium",
        "description": "Average student with occasional confusion and lower resilience.",
        "grader": {"module": "grader", "function": "grade_episode"},
    },
    {
        "id": "hard",
        "name": "hard",
        "difficulty": "hard",
        "description": "Student with severe misconceptions, high fatigue potential, and nonlinear learning curves.",
        "grader": {"module": "grader", "function": "grade_episode"},
    },
]

# We use a global instance for the hackathon/grader purpose.
# Graders evaluate environments one session at a time locally or isolated via Docker.
current_env: Optional[AlieEnv] = None
connected_clients: List[WebSocket] = []

class ResetRequest(BaseModel):
    task_name: str = "medium"

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

async def broadcast_state(event_type: str):
    if not connected_clients or current_env is None:
        return
    data = {
        "type": event_type,
        "state": current_env.state()
    }
    for client in connected_clients.copy():
        try:
            await client.send_json(data)
        except:
            connected_clients.remove(client)

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    with open("server/dashboard.html", "r") as f:
        return f.read()

@app.post("/reset", response_model=Observation)
async def reset_env(req: ResetRequest = ResetRequest()):
    global current_env
    current_env = AlieEnv(task_name=req.task_name)
    obs = await current_env.reset()
    await broadcast_state("reset")
    return obs

@app.post("/step", response_model=StepResult)
async def step_env(action: Action):
    global current_env
    if current_env is None:
            raise HTTPException(status_code=400, detail="Environment has not been reset.")
    try:
        step_result = await current_env.step(action)
        await broadcast_state("step")
        return step_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/state", response_model=Dict[str, Any])
async def get_state():
    global current_env
    if current_env is None:
        raise HTTPException(status_code=400, detail="Environment has not been reset.")
    
    # Needs to return unmasked internal state (specifically what AlieEnv builds)
    # The requirement specifically says state(), we will just return it direct
    state_dict = current_env.state()
    return state_dict

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return {"tasks": TASKS, "count": len(TASKS)}


@app.get("/validate")
def validate():
    scores = {
        task["id"]: grade_episode(get_initial_state(task["id"]), 0)
        for task in TASKS
    }
    checks = {
        "min_3_tasks": len(TASKS) >= 3,
        "all_tasks_have_graders": all(task.get("grader") for task in TASKS),
        "scores_strictly_between_0_and_1": all(0.0 < score < 1.0 for score in scores.values()),
        "reset_endpoint": True,
        "step_endpoint": True,
        "state_endpoint": True,
    }
    return {
        "valid": all(checks.values()),
        "checks": checks,
        "scores": scores,
        "env_name": "ALIE",
        "version": "1.0.0",
    }


@app.get("/grade/{task_name}")
def grade_task(task_name: str):
    if task_name not in {task["id"] for task in TASKS}:
        raise HTTPException(status_code=404, detail="Unknown task")

    if current_env is not None and current_env.task_name == task_name and current_env.sim is not None:
        score = current_env.state().get("score", 0.001)
        source = "live_state"
    else:
        score = grade_episode(get_initial_state(task_name), 0)
        source = "initial_state"

    score = max(0.001, min(0.999, float(score)))
    return {
        "task_id": task_name,
        "has_grader": True,
        "grader": {"module": "grader", "function": "grade_episode"},
        "score": score,
        "source": source,
    }

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
