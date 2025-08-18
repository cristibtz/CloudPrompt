import asyncio
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from cloudprompt.agent.router_agent import execute_provider
from app.database.db import get_db
from app.models.user import User
from app.models.prompts import Prompt
import json, ast

app = FastAPI()

router_v1 = APIRouter(prefix="/api/v1", tags=["v1"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React dev server
        "http://127.0.0.1:3000",   # Alternative localhost
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173",   # Alternative Vite
        "http://192.168.100.11:5173", # Local network Vite
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class Request(BaseModel):
    prompt: str
    provider: str

@router_v1.post("/execute")
async def execute(request: Request, db: Session = Depends(get_db)):
    user_input = request.prompt
    provider = request.provider
    
    if not user_input:
        return {"error": "Prompt cannot be empty."}
    if not provider:
        return {"error": "Provider cannot be empty."}
    
    try:
        result = await execute_provider(provider, user_input)
        output = result.output
        return json.loads(output)
        
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from agent.", "received_output": output}
    except Exception as e:
        # Return the actual error message for debugging
        return {"error": f"Internal server error: {str(e)}"}

@router_v1.get("/health")
async def health_check():
    try:
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

app.include_router(router_v1)

@app.get("/")
async def root():
    return {"message": "CloudPrompt API", "version": "0.0.1"}
