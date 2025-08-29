from fastapi import HTTPException, Header, APIRouter, Request, Depends
from dotenv import load_dotenv
import os, json, base64
from pydantic import BaseModel
from typing import Dict, Any

from app.auth import auth
from app.utils.check_admin_role import check_admin_role
from app.utils.get_id_by_kc_id import get_id_by_kc_id

from app.database.db import get_db
from app.models.user import User
from app.models.prompts import Prompt
from app.models.credentials import Credential

from app.utils.crypto import encrypt_data

key = bytes.fromhex(os.getenv("ENCRYPTION_KEY"))

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../','.env'))

router = APIRouter()

class CreateCredentialRequest(BaseModel):
    """Request model for creating new credentials."""
    provider: str 
    name: str 
    data: Dict[str, Any]

providers = ["aws", "azure", "gcp", "proxmox"]
max_creds_per_user = 5

@router.post("/", 
             tags=["Credential Management"], 
             dependencies=[Depends(auth.valid_access_token)], 
             summary="Create new credentials")
async def create_credential(request: CreateCredentialRequest,
    token_data: Dict = Depends(auth.valid_access_token)
    ):
    name = request.name.strip() if request.name else ""
    provider = request.provider
    data = request.data

    if not name:
        raise HTTPException(
            status_code=400, 
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_NAME",
                    "message": "Credential name is required"
                }
            }
        )

    if not provider or not data:
        raise HTTPException(
            status_code=400, 
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "Provider and credential data are required"
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

    if provider == "aws":
        if "AWS_ACCESS_KEY" not in data or "AWS_SECRET_ACCESS_KEY" not in data:
            raise HTTPException(
                status_code=400, 
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid credential format for AWS"
                    }
                }
            )
        if not data.get("AWS_ACCESS_KEY") or not data.get("AWS_SECRET_ACCESS_KEY"):
            raise HTTPException(
                status_code=400, 
                detail={
                    "success": False,
                    "error": {
                        "code": "EMPTY_CREDENTIALS",
                        "message": "Credential values cannot be empty"
                    }
                }
            )
    elif provider == "proxmox":
        if "host" not in data or "username" not in data or "password" not in data:
            raise HTTPException(
                status_code=400, 
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid credential format for Proxmox"
                    }
                }
            )
        if not data.get("host") or not data.get("username") or not data.get("password"):
            raise HTTPException(
                status_code=400, 
                detail={
                    "success": False,
                    "error": {
                        "code": "EMPTY_CREDENTIALS",
                        "message": "Credential values cannot be empty"
                    }
                }
            )

    try:
        keycloak_id = token_data.get("sub")
        
        user_id = get_id_by_kc_id(keycloak_id)

        db = next(get_db())

        existing_cred = db.query(Credential).filter(
            Credential.user_id == user_id,
            Credential.name == name
        ).first()
        if existing_cred:
            raise HTTPException(
                status_code=400, 
                detail={
                    "success": False,
                    "error": {
                        "code": "DUPLICATE_NAME",
                        "message": "Credential name already exists"
                    }
                }
            )

        existing_creds_count = db.query(Credential).filter(
            Credential.user_id == user_id,
            Credential.provider == provider
        ).count()
        if existing_creds_count >= max_creds_per_user:
            raise HTTPException(
                status_code=400, 
                detail={
                    "success": False,
                    "error": {
                        "code": "LIMIT_EXCEEDED",
                        "message": "Maximum credentials limit reached"
                    }
                }
            )
        
        new_cred = Credential(
            user_id=user_id,
            provider=provider,
            name=name,
            data=encrypt_data(key, json.dumps(data))
        )
        db.add(new_cred)
        db.commit()
        db.refresh(new_cred)
        
        return {
            "success": True,
            "message": "Credential created successfully",
            "data": {
                "id": new_cred.id,
                "name": new_cred.name,
                "provider": new_cred.provider
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
                    "message": "Failed to create credential"
                }
            }
        )

@router.get("/", 
            tags=["Credential Management"], 
            dependencies=[Depends(check_admin_role)], 
            summary="Get all credentials (Admin only)")
async def get_credentials():
    try:
        db = next(get_db())
        creds = db.query(Credential).all()
        return {
            "success": True,
            "data": [{"id": c.id, "name": c.name, "provider": c.provider, "user_id": c.user_id} for c in creds],
            "message": "Credentials retrieved successfully"
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/user", 
            tags=["Credential Management"], 
            dependencies=[Depends(auth.valid_access_token)], 
            summary="Get user credentials")
async def get_user_credentials(token_data: Dict = Depends(auth.valid_access_token)):
    try:
        keycloak_id = token_data.get("sub")
        user_id = get_id_by_kc_id(keycloak_id)
        db = next(get_db())
        creds = db.query(Credential).filter(Credential.user_id == user_id).all()
        return {
            "success": True,
            "data": [{"id": c.id, "name": c.name, "provider": c.provider} for c in creds],
            "message": "User credentials retrieved successfully"
        }
    except Exception:
        raise HTTPException(
            status_code=500, 
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to retrieve credentials"
                }
            }
        )

@router.get("/{cred_id}", 
            tags=["Credential Management"], 
            dependencies=[Depends(auth.valid_access_token)], 
            summary="Get credential details")
async def get_credential_details(
    cred_id: int,
    token_data: Dict = Depends(auth.valid_access_token)
):
    try:
        keycloak_id = token_data.get("sub")
        user_id = get_id_by_kc_id(keycloak_id)
        db = next(get_db())
        cred = db.query(Credential).filter(Credential.id == cred_id, Credential.user_id == user_id).first()
        if not cred:
            raise HTTPException(
                status_code=404, 
                detail={
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Credential not found"
                    }
                }
            )
        return {
            "success": True,
            "data": {
                "id": cred.id,
                "name": cred.name,
                "provider": cred.provider
            },
            "message": "Credential details retrieved successfully"
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
                    "message": "Failed to retrieve credential details"
                }
            }
        )

@router.delete("/{cred_id}", 
               tags=["Credential Management"],
               dependencies=[Depends(auth.valid_access_token)], 
               summary="Delete credential")
async def delete_credential(
    cred_id: int,
    token_data: Dict = Depends(auth.valid_access_token)
):
    try:
        keycloak_id = token_data.get("sub")
        user_id = get_id_by_kc_id(keycloak_id)
        db = next(get_db())
        cred = db.query(Credential).filter(Credential.id == cred_id, Credential.user_id == user_id).first()
        if not cred:
            raise HTTPException(
                status_code=404, 
                detail={
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Credential not found"
                    }
                }
            )
        cred_name = cred.name
        db.delete(cred)
        db.commit()
        return {
            "success": True,
            "message": "Credential deleted successfully",
            "data": {
                "deleted_credential": cred_name
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
                    "message": "Failed to delete credential"
                }
            }
        )