from fastapi import HTTPException, Depends

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../','.env'))

from app.database.db import get_db
from app.models.user import User
from app.models.prompts import Prompt
from app.models.credentials import Credential

def get_id_by_kc_id(keycloak_id):
    try:
        db = next(get_db())
        user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user.id
    except Exception as e:
        #print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")