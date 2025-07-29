import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from cloudprompt.agent.router_agent import CloudRouterAgent
import json, ast

app = FastAPI()

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
