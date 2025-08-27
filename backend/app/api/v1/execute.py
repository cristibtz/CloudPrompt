from fastapi import APIRouter, HTTPException, Depends
from app.auth import auth
from cloudprompt.agent.router_agent import execute_provider
from app.models.responses import ExecuteResponse, ErrorDetail
from app.utils.get_id_by_kc_id import get_id_by_kc_id
from app.database.db import get_db
from app.models.credentials import Credential
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import json, base64

router = APIRouter()

class ExecuteRequest(BaseModel):
    """Request model for command execution."""
    prompt: str = Field(..., 
                       description="Natural language command to execute",
                       example="List all EC2 instances in us-east-1",
                       min_length=1,
                       max_length=1000)
    provider: str = Field(..., 
                         description="Cloud provider to execute the command on",
                         example="aws")
    credentials: Optional[str] = Field(None,
                                     description="Name of the credential set to use for authentication",
                                     example="my-aws-credentials")

    class Config:
        schema_extra = {
            "example": {
                "prompt": "List all running EC2 instances",
                "provider": "aws", 
                "credentials": "my-aws-prod-creds"
            }
        }

@router.post("/execute", 
             dependencies=[Depends(auth.valid_access_token)], 
             response_model=ExecuteResponse,
             summary="Execute cloud command",
             description="Execute a natural language command on the specified cloud provider",
             responses={
                 200: {
                     "description": "Command executed successfully",
                     "content": {
                         "application/json": {
                             "example": {
                                 "success": True,
                                 "data": {"instances": [{"id": "i-123", "state": "running"}]},
                                 "provider": "aws",
                                 "message": "Prompt executed successfully"
                             }
                         }
                     }
                 },
                 400: {
                     "description": "Bad request - validation error",
                     "content": {
                         "application/json": {
                             "examples": {
                                 "missing_prompt": {
                                     "summary": "Missing prompt",
                                     "value": {
                                         "success": False,
                                         "error": {
                                             "code": "INVALID_INPUT",
                                             "message": "Prompt is required"
                                         }
                                     }
                                 },
                                 "missing_credentials": {
                                     "summary": "Missing credentials",
                                     "value": {
                                         "success": False,
                                         "error": {
                                             "code": "INVALID_CREDENTIALS", 
                                             "message": "Provide credentials set"
                                         }
                                     }
                                 },
                                 "unsupported_provider": {
                                     "summary": "Unsupported provider",
                                     "value": {
                                         "success": False,
                                         "error": {
                                             "code": "UNSUPPORTED_PROVIDER",
                                             "message": "Provider not supported"
                                         }
                                     }
                                 }
                             }
                         }
                     }
                 },
                 401: {
                     "description": "Unauthorized - invalid or missing token"
                 },
                 500: {
                     "description": "Internal server error",
                     "content": {
                         "application/json": {
                             "example": {
                                 "success": False,
                                 "error": {
                                     "code": "EXECUTION_FAILED",
                                     "message": "Prompt execution failed"
                                 }
                             }
                         }
                     }
                 }
             })
async def execute(request: ExecuteRequest, token_data: Dict = Depends(auth.valid_access_token)):
    """
    Execute a natural language command on a cloud provider.
    
    This endpoint processes natural language prompts and executes them on the specified
    cloud provider using the provided credentials. The system supports multiple cloud
    providers including AWS, Azure, GCP, and Proxmox.
    
    Args:
        request: ExecuteRequest containing the prompt, provider, and credentials
        token_data: Authentication token data (automatically injected)
    
    Returns:
        ExecuteResponse: Result of the command execution including data and status
        
    Raises:
        HTTPException: For validation errors, missing credentials, or execution failures
    """
    
    providers = ["aws", "azure", "gcp", "proxmox"]

    user_input = request.prompt.strip() if request.prompt else ""
    provider = request.provider
    credentials_name = request.credentials

    if not user_input:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "Prompt is required"
                }
            }
        )
    
    if not credentials_name:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Provide credentials set"
                }
            }
        )

    if not provider:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_PROVIDER", 
                    "message": "Provider is required"
                }
            }
        )
    
    if provider not in providers:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "UNSUPPORTED_PROVIDER",
                    "message": "Provider not supported"
                }
            }
        )

    credentials_data = None
    if credentials_name:
        try:
            keycloak_id = token_data.get("sub")
            user_id = get_id_by_kc_id(keycloak_id)
            
            db = next(get_db())
            credential = db.query(Credential).filter(
                Credential.user_id == user_id,
                Credential.name == credentials_name,
                Credential.provider == provider
            ).first()
            
            if credential:
                credentials_data = json.loads(base64.b64decode(credential.data).decode('utf-8'))
        except Exception:
            pass
    
    try:
        result = await execute_provider(provider, user_input, credentials_data)
        output = result.output
        
        try:
            parsed_response = json.loads(output)
            return {
                "success": True,
                "data": parsed_response,
                "provider": provider,
                "message": "Prompt executed successfully"
            }
        except json.JSONDecodeError:
            return {
                "success": True,
                "data": {"message": output},
                "provider": provider,
                "message": "Prompt executed successfully"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "EXECUTION_FAILED",
                    "message": "Prompt execution failed"
                }
            }
        )