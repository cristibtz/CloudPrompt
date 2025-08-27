from fastapi import HTTPException, Depends
from app.auth import auth

def check_admin_role(data: dict = Depends(auth.valid_access_token)):
    roles = data.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(status_code=403, detail="Forbidden")
    return data