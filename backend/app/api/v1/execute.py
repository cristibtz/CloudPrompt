from fastapi import APIRouter, HTTPException
from cloudprompt.agent.router_agent import execute_provider
from pydantic import BaseModel
import json

router = APIRouter()

class Request(BaseModel):
    prompt: str
    provider: str

@router.post("/execute")
async def execute(request: Request):
    
    user_input = request.prompt

    provider = request.provider
    
    if not user_input:
        return {"response": "Prompt cannot be empty."}
    if not provider:
        return {"response": "Provider cannot be empty."}
    
    # Verify input data

    try:
        
        result = await execute_provider(provider, user_input)
        output = result.output
        return {"response": json.loads(output)}
        
    except json.JSONDecodeError:
        return {"response": "Invalid JSON response from agent.", "received_output": output}
    except Exception as e:
        # Return the actual error message for debugging
        return HTTPException(
            status_code=500,
            detail=f"An error occurred while executing the command: {str(e)}")