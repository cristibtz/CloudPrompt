from fastapi import HTTPException, Depends
from app.auth import auth
from typing import Dict

async def check_admin_role(token_data: Dict = Depends(auth.valid_access_token)):
    try:
        roles = token_data.get("realm_access", {}).get("roles", [])
        if "admin" not in roles:
            raise HTTPException(status_code=403, detail="Access denied")
        return token_data
    except KeyError:
        raise HTTPException(status_code=403, detail="Access denied")