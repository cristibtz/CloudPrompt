import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cloudprompt.agent.router_agent import CloudRouterAgent
import json, ast

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React dev server
        "http://127.0.0.1:3000",   # Alternative localhost
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173",   # Alternative Vite
        "http://192.168.100.179:5173", # Local network Vite
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

router = CloudRouterAgent()

class Request(BaseModel):
    prompt: str


@app.post("/api/v1/execute")
async def route_and_execute(request: Request):

    user_input = request.prompt
    
    if not user_input:

        return {"error": "Prompt cannot be empty."}

    try:
        result = await router.route_and_execute(user_input)

        output = result.output

        return json.loads(output)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from agent."}
    except Exception as e:
        return {"error": f"Internal server error"}
        print(f"Error: {e}")

@app.get("/api/v1/health")
async def health_check():

    try:
        return {"status": "ok"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
