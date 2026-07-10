# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="PC Automation Control Center")

# Simple API Key Authentication
API_KEY = os.environ.get("AUTH_SECRET_KEY", "your-super-secure-shared-key")
api_key_header = APIKeyHeader(name="X-Auth-Token")

async def verify_auth(token: str = Depends(api_key_header)):
    if token != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Auth Token",
        )
    return token

# Global in-memory state to hold the current command and execution status
current_command = {"command": None, "status": "idle"}

class VoicePayload(BaseModel):
    text: str

class StatusUpdate(BaseModel):
    status: str

@app.post("/api/command", dependencies=[Depends(verify_auth)])
async def receive_voice_command(payload: VoicePayload):
    raw_text = payload.text.lower()
    
    # AI Parsing Mockup: Translate natural language into structured JSON steps
    # In production, replace this block with your AI API call (Gemini/OpenAI)
    # prompt: "Convert this command into a JSON containing 'action' and 'target': {raw_text}"
    structured_action = {"action": "unknown", "target": ""}
    
    if "chrome" in raw_text or "browser" in raw_text:
        structured_action = {"action": "open", "target": "chrome"}
    elif "notepad" in raw_text:
        structured_action = {"action": "open", "target": "notepad"}
    elif "volume up" in raw_text:
        structured_action = {"action": "volume", "target": "up"}
        
    current_command["command"] = structured_action
    current_command["status"] = "pending"
    
    return {"message": "Command queued successfully", "parsed": structured_action}

@app.get("/api/agent/poll", dependencies=[Depends(verify_auth)])
async def agent_poll():
    """Local EXE hits this endpoint to see if there is work to do."""
    if current_command["status"] == "pending":
        return {"has_command": True, "data": current_command["command"]}
    return {"has_command": False}

@app.post("/api/agent/status", dependencies=[Depends(verify_auth)])
async def update_agent_status(payload: StatusUpdate):
    """Local EXE reports back when done."""
    current_command["status"] = payload.status
    if payload.status == "done":
        current_command["command"] = None
    return {"status": "acknowledged"}

@app.get("/api/status")
async def get_system_status():
    """Frontend polls this to show current execution state."""
    return current_command
