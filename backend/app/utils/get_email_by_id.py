from fastapi import HTTPException, Depends

from keycloak import KeycloakAdmin

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../','.env'))

def get_email_by_id(user_id):
    try:        
        server_url = os.getenv("KEYCLOAK_SERVER_URL")
        admin_username = os.getenv("KEYCLOAK_ADMIN_USERNAME")
        admin_password = os.getenv("KEYCLOAK_ADMIN_PASSWORD")
                
        keycloak_admin = KeycloakAdmin(
            server_url=server_url,
            username=admin_username,
            password=admin_password,
            realm_name="cloudprompt",
            user_realm_name="master",
            verify=False
        )

        user = keycloak_admin.get_user(user_id)
        return user.get("email")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error")
