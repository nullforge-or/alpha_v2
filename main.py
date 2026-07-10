from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

app = FastAPI(title="Jarvis Core Backend")

# --- CORS CONFIGURATION ---
# Allows your Cloudflare frontend to talk to this Render backend securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AUTHENTICATION ---
# Pulls from Render Environment Variables, falls back to your hardcoded token
API_KEY = os.environ.get("AUTH_SECRET_KEY", "yashansh-pc-auto-agent-8f72c9a1")
api_key_header = APIKeyHeader(name="X-Auth-Token")

async def verify_auth(token: str = Depends(api_key_header)):
    if token != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized Access. Invalid Token.",
        )
    return token

# --- SYSTEM STATE ---
# Holds the single command in memory until the local node pulls it
current_command = {"target": None, "status": "idle"}

class VoicePayload(BaseModel):
    text: str

class StatusUpdate(BaseModel):
    status: str

# --- API ROUTES ---

@app.get("/")
async def root_status():
    """Front door routing - fixes the 'Not Found' error."""
    return {"system": "Jarvis Render Node Online", "status": "operational"}

@app.post("/api/command", dependencies=[Depends(verify_auth)])
async def receive_voice_command(payload: VoicePayload):
    """Frontend sends the raw voice text here."""
    # We pass the raw text directly into the queue. 
    # The local PC agent will handle the AI processing.
    current_command["target"] = payload.text
    current_command["status"] = "pending"
    
    return {"message": "Command queued successfully", "raw_text": payload.text}

@app.get("/api/agent/poll", dependencies=[Depends(verify_auth)])
async def agent_poll():
    """Local PC agent constantly hits this to check for work."""
    if current_command["status"] == "pending":
        return {"has_command": True, "data": current_command}
    return {"has_command": False}

@app.post("/api/agent/status", dependencies=[Depends(verify_auth)])
async def update_agent_status(payload: StatusUpdate):
    """Local PC agent reports back when it starts working and when it finishes."""
    current_command["status"] = payload.status
    
    # Clear the queue once the task is complete or if it crashes locally
    if payload.status in ["done", "failed"]:
        current_command["target"] = None
        
    return {"status": "acknowledged"}

@app.get("/api/status")
async def get_system_status():
    """Frontend polls this to update the UI (Running, Done, Failed)."""
    return current_command
