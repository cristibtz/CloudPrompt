from fastapi import APIRouter, HTTPException, Depends
from app.auth import auth
from cloudprompt.agent.router_agent import execute_provider
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json

router = APIRouter()

class Request(BaseModel):
    prompt: str
    provider: str
    credentials: Optional[Dict[str, Any]] = None

@router.post("/execute", dependencies=[Depends(auth.valid_access_token)])
async def execute(request: Request):
    
    providers = ["aws", "azure", "gcp", "proxmox"]

    user_input = request.prompt

    provider = request.provider
    
    if not user_input:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Prompt cannot be empty",
                "provider": provider,
                "received_output": None
            }
        )
    if not provider:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Provider cannot be empty",
                "provider": None,
                "received_output": None
            }
        )
    
    # Verify input data
    if provider not in providers:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": f"Invalid provider '{provider}'. Supported providers are: {', '.join(providers)}",
                "provider": provider,
                "received_output": None
            }
        )
    
    try:
        
        result = await execute_provider(provider, user_input, request.credentials)
        output = result.output
        
        # Try to parse as JSON first
        try:
            parsed_response = json.loads(output)
            return {
                "success": True,
                "response": parsed_response,
                "provider": provider
            }
        except json.JSONDecodeError:
            # If it's not JSON, treat it as plain text response (this is valid!)
            return {
                "success": True,
                "response": {"message": output},
                "provider": provider,
                "is_plain_text": True
            }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Return structured error with details
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Internal server error: {str(e)}",
                "provider": provider,
                "received_output": None
            }
        )