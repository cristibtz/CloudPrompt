import asyncio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import execute
from app.api.v1 import users, credentials, prompts
import json, ast
from app.auth import auth

# FastAPI app with comprehensive documentation
app = FastAPI(
    title="CloudPrompt API",
    description="Cloud automation platform for executing natural language commands across AWS, Azure, GCP, and Proxmox.",
    version="0.0.2",
    contact={
        "name": "CloudPrompt Support",
        "url": "https://github.com/cristibtz/CloudPrompt",
    }
)

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
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/v1/users", tags=["User Management"])
app.include_router(credentials.router, prefix="/api/v1/credentials", tags=["Credential Management"])
app.include_router(prompts.router, prefix="/api/v1/prompts", tags=["Prompt Management"])
app.include_router(execute.router, prefix="/api/v1", tags=["Prompt Execution"])

@app.get("/", 
         dependencies=[Depends(auth.valid_access_token)],
         summary="API information and version",
         tags=["System"])
async def root():

    try:
        return {"response": "CloudPrompt API", "version": "0.0.2"}
    except Exception as e:
        return {"response": f"Internal Server Error: {str(e)}"}

@app.get("/api/v1/health",
         summary="Health check",
         tags=["System"])
async def health_check():

    try:
        return {"response": "ok"}
    except Exception as e:
        return {"response": f"Internal Server Error: {str(e)}"}