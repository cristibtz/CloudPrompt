import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from llmcloud.agent.agent import run_aws_agent
import json, ast

app = FastAPI()

class Request(BaseModel):
    prompt: str

@app.post("/api/v1/aws")
async def aws_management(request: Request):
    user_input = request.prompt
    if not user_input:
        return {"error": "Prompt cannot be empty."}
    try:
        result = await run_aws_agent(user_input)

        output = result.output

        return json.loads(output)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from agent."}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}