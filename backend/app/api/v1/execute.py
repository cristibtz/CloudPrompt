from fastapi import APIRouter, HTTPException, Depends
from app.auth import auth
from cloudprompt.agent.router_agent import execute_provider
from cloudprompt.agent.agent import clear_user_session
from app.utils.get_id_by_kc_id import get_id_by_kc_id
from app.database.db import get_db
from app.models.credentials import Credential
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import json, base64

from app.utils.crypto import decrypt_data

from dotenv import load_dotenv
import os
load_dotenv(os.path.join(os.path.dirname(__file__), '../../','.env'))

key = bytes.fromhex(os.getenv("ENCRYPTION_KEY")) 

router = APIRouter()

class ExecuteRequest(BaseModel):
    """Request model for prompt execution."""
    prompt: str
    provider: str
    credentials_name: str

@router.post("/execute", 
             dependencies=[Depends(auth.valid_access_token)], 
             tags=["Prompt Execution"],
             summary="Execute prompt")
async def execute(request: ExecuteRequest, token_data: Dict = Depends(auth.valid_access_token)):

    providers = ["aws", "azure", "gcp", "proxmox"]

    user_input = request.prompt.strip() if request.prompt else ""
    provider = request.provider
    credentials_name = request.credentials_name

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
                credentials_data = json.loads(decrypt_data(key, credential.data))
        except Exception:
            pass
    
    try:
        # Get keycloak_id for session management
        keycloak_id = token_data.get("sub")
        
        result = await execute_provider(provider, user_input, credentials_data, keycloak_id=keycloak_id)
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
        print(f"Execution error: {str(e)}")
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

@router.post("/clear_session", 
             dependencies=[Depends(auth.valid_access_token)], 
             tags=["Session Management"],
             summary="Clear user session")
async def clear_session(token_data: Dict = Depends(auth.valid_access_token)):
    """Clear the current user's cloud provider session tokens."""
    try:
        keycloak_id = token_data.get("sub")
        
        # Clear the user's session
        clear_user_session(keycloak_id)
        
        return {
            "success": True,
            "message": "Session cleared successfully",
            "data": {
                "session_id": keycloak_id,
                "action": "session_cleared"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "SESSION_CLEAR_FAILED",
                    "message": f"Failed to clear session: {str(e)}"
                }
            }
        )