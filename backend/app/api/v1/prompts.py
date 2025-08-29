from fastapi import HTTPException, Header, APIRouter, Depends

from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import Dict, Any, Literal
import os

from app.auth import auth
from app.utils.check_admin_role import check_admin_role
from app.utils.get_id_by_kc_id import get_id_by_kc_id

from app.database.db import get_db
from app.models.user import User
from app.models.prompts import Prompt
from app.models.credentials import Credential

load_dotenv(os.path.join(os.path.dirname(__file__), "../../../", ".env"))

router = APIRouter()

@router.get("/",
            dependencies=[Depends(check_admin_role)],
            tags=["Prompt Management"],
            summary="List all saved prompts (Admin only)"
            )
async def get_prompts():
    try:
        db = next(get_db())
        try:
            prompts = db.query(Prompt).all()
            return {
                "success": True,
                "data": [
                    {
                        "id": prompt.id,
                        "user_id": prompt.user_id,
                        "prompt": prompt.prompt,
                        "response": prompt.response,
                        "provider": prompt.provider,
                        "created_at": prompt.created_at
                    } for prompt in prompts
                ],
                "message": "Prompts retrieved successfully."
            }
        finally:
            db.close()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/user", 
            dependencies=[Depends(auth.valid_access_token)],
            tags=["Prompt Management"],
            summary="List saved prompts for the authenticated user"
            )
async def get_user_prompts(token_data: Dict = Depends(auth.valid_access_token)):
    try:
        keycloak_id = token_data.get("sub")
        user_id = get_id_by_kc_id(keycloak_id)

        db = next(get_db())
        try:
            prompts = db.query(Prompt).filter(Prompt.user_id == user_id).all()
            return {
                "success": True,
                "data": [
                    {
                        "id": prompt.id,
                        "prompt": prompt.prompt,
                        "response": prompt.response,
                        "provider": prompt.provider,
                        "created_at": prompt.created_at
                    } for prompt in prompts
                ],
                "message": "User prompts retrieved successfully."
            }
        finally:
            db.close()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{prompt_id}", 
            dependencies=[Depends(auth.valid_access_token)],
            tags=["Prompt Management"],
            summary="List prompt using id for the authenticated user"
            )
async def get_prompt_detail(prompt_id: int, token_data: Dict = Depends(auth.valid_access_token)):
    try:
        keycloak_id = token_data.get("sub")

        user_id = get_id_by_kc_id(keycloak_id)

        db = next(get_db())
        try:
            prompt = db.query(Prompt).filter(
                Prompt.id == prompt_id,
                Prompt.user_id == user_id
            ).first()
            if not prompt:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "success": False,
                        "error": {
                            "code": "PROMPT_NOT_FOUND",
                            "message": "Prompt not found"
                        }
                    }
                )
            return {
                "success": True,
                "data": {
                    "id": prompt.id,
                    "prompt": prompt.prompt,
                    "response": prompt.response,
                    "provider": prompt.provider,
                    "created_at": prompt.created_at
                },
                "message": "Prompt retrieved successfully."
            }
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

providers = ["aws", "azure", "gcp", "proxmox"]
max_prompts_per_user = 20

class CreatePromptRequest(BaseModel):
    prompt: str 
    response: str
    provider: str

@router.post("/",
            tags=["Prompt Management"],
            dependencies=[Depends(auth.valid_access_token)],
            summary="Save a prompt"
            )
async def create_prompt(request: CreatePromptRequest,
    token_data: Dict = Depends(auth.valid_access_token)
    ):

    prompt = request.prompt
    response = request.response
    provider = request.provider

    if not prompt:
        raise HTTPException(
            status_code=400, 
            detail={
                "success": False,
                "error": {
                    "code": "MISSING_PROMPT",
                    "message": "Prompt text is required"
                }
            }
        )

    if not response:
        raise HTTPException(
            status_code=400, 
            detail={
                "success": False,
                "error": {
                    "code": "MISSING_RESPONSE",
                    "message": "Response text is required"
                }
            }
        )

    if not provider:
        raise HTTPException(
            status_code=400, 
            detail={
                "success": False,
                "error": {
                    "code": "MISSING_PROVIDER",
                    "message": "Provider data is required"
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

    try:
        keycloak_id = token_data.get("sub")

        user_id = get_id_by_kc_id(keycloak_id)

        db = next(get_db())

        existing_prompts_count = db.query(Prompt).filter(
            Prompt.user_id == user_id
        ).count()

        if existing_prompts_count >= max_prompts_per_user:
            raise HTTPException(
                status_code=400, 
                detail={
                    "success": False,
                    "error": {
                        "code": "LIMIT_EXCEEDED",
                        "message": "Maximum stored prompts limit reached"
                    }
                }
            )
        
        new_prompt = Prompt(
            user_id=user_id,
            prompt=prompt,
            response=response,
            provider=provider
        )
        db.add(new_prompt)
        db.commit()
        db.refresh(new_prompt)
        
        return {
            "success": True,
            "message": "Prompt saved successfully",
            "data": {
                "id": new_prompt.id,
                "name": new_prompt.prompt,
                "provider": new_prompt.provider,
                "created_at": new_prompt.created_at
            }
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, 
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to save prompt"
                }
            }
        )

@router.delete("/{prompt_id}", 
               dependencies=[Depends(auth.valid_access_token)],
               tags=["Prompt Management"],
               summary="Delete a saved prompt"
               )
async def delete_prompt(prompt_id: int, token_data: Dict = Depends(auth.valid_access_token)):
    try:
        keycloak_id = token_data.get("sub")

        user_id = get_id_by_kc_id(keycloak_id)

        db = next(get_db())
        prompt = db.query(Prompt).filter(
            Prompt.id == prompt_id,
            Prompt.user_id == user_id
        ).first()

        if not prompt:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": {
                        "code": "PROMPT_NOT_FOUND",
                        "message": "Prompt not found"
                    }
                }
            )

        db.delete(prompt)
        db.commit()

        return {
            "success": True,
            "message": "Prompt deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to delete prompt"
                }
            }
        )