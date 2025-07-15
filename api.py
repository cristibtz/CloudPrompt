import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from client.client import run_aws_agent
import json, ast

app = FastAPI()

class Request(BaseModel):
    prompt: str

@app.post("/api/v1/aws/ec2")
async def ec2_management(request: Request):
    user_input = request.prompt
    if not user_input:
        return {"error": "Prompt cannot be empty."}
    try:
        result = await run_aws_agent(user_input)
        return json.loads(result)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from agent."}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}