from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from env.models import Action, Observation, StepResult
from env.alie_env import AlieEnv
from starlette.staticfiles import StaticFiles
import os

app = FastAPI(title="ALIE Environment API")

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

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
