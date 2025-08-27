import asyncio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import execute
from app.api.v1 import users, credentials
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
# app.include_router(prompts.router, prefix="/api/v1", tags=["prompts"])
app.include_router(execute.router, prefix="/api/v1", tags=["Prompt Execution"])

@app.get("/", 
         dependencies=[Depends(auth.valid_access_token)],
         summary="Root endpoint",
         description="Returns basic API information and version.",
         response_description="API information with version number",
         tags=["System"])
async def root():
    """
    Get basic API information.
    
    Returns the API name and current version number.
    Requires authentication to access.
    """
    try:
        return {"response": "CloudPrompt API", "version": "0.0.2"}
    except Exception as e:
        return {"response": f"Internal Server Error: {str(e)}"}

@app.get("/api/v1/health",
         summary="Health check",
         description="Check if the API is running and responsive.",
         response_description="API health status",
         tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the operational status of the API.
    Does not require authentication.
    
    Returns:
        dict: Status response indicating if the API is operational
    """
    try:
        return {"response": "ok"}
    except Exception as e:
        return {"response": f"Internal Server Error: {str(e)}"}