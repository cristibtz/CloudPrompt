from fastapi import HTTPException, Depends

from keycloak import KeycloakAdmin
from app.utils.keycloak_admin import init_keycloak_admin

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../','.env'))

def get_email_by_id(user_id):
    try:        
        keycloak_admin = init_keycloak_admin()

        user = keycloak_admin.get_user(user_id)

        return user.get("email")
        
    except Exception as e:
        #print(f"❌ Error: {str(e)}")
        #import traceback
        #print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error")
