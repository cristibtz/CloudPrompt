from fastapi import HTTPException, Header, APIRouter, Request, Depends
from dotenv import load_dotenv
import os, json, base64
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.auth import auth
from app.utils.check_admin_role import check_admin_role
from app.utils.get_id_by_kc_id import get_id_by_kc_id

from app.database.db import get_db
from app.models.user import User
from app.models.prompts import Prompt
from app.models.credentials import Credential

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../','.env'))

router = APIRouter()

class Request(BaseModel):
    provider: str
    data: Dict[str, Any]

providers = ["aws", "azure", "gcp", "proxmox"]
max_creds_per_user = 5

@router.post("/", tags=["credentials"], dependencies=[Depends(auth.valid_access_token)])
async def create_credential(request: Request,
    token_data: Dict = Depends(auth.valid_access_token)
    ):
    if request.provider is None or request.data is None:
        raise HTTPException(status_code=400, detail=f"Bad request")

    if request.provider not in providers:
        raise HTTPException(status_code=400, detail=f"Bad request")
    try:
        keycloak_id = token_data.get("sub")
        
        user_id = get_id_by_kc_id(keycloak_id)

        db = next(get_db())

        creds = db.query(Credential).filter(Credential.user_id == user_id, Credential.provider == request.provider).all()
        if len(creds) >= max_creds_per_user:
            raise HTTPException(status_code=400, detail=f"Maximum number of credentials reached for provider {request.provider}")
        
        new_cred = Credential(
            user_id=user_id,
            provider=request.provider,
            data=base64.b64encode(json.dumps(request.data).encode('utf-8')).decode('utf-8')
        )
        db.add(new_cred)
        db.commit()
        db.refresh(new_cred)
        return {
            "success": True,
            "response": f"Credential created successfully for provider {request.provider}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")