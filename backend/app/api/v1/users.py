import hashlib
import hmac
from fastapi import HTTPException, Header, APIRouter, Request, Depends
from dotenv import load_dotenv
import os, json

from app.utils.get_email_by_id import get_email_by_id
from app.utils.check_admin_role import check_admin_role

from app.database.db import get_db
from app.models.user import User
from app.models.prompts import Prompt
from app.models.credentials import Credential

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../','.env'))

router = APIRouter()

@router.post("/keycloak-webhook", tags=["users"])
async def webhook_handler(
    request: Request,
    x_keycloak_signature: str = Header(None, alias="X-Keycloak-Signature")
):
    try:
        body = await request.body()

        shared_secret = os.getenv("WEBHOOK_SECRET")

        if x_keycloak_signature:
            expected_signature = hmac.new(
                shared_secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()

            signature = x_keycloak_signature   

            if not hmac.compare_digest(signature, expected_signature):
                raise HTTPException(status_code=401, detail="Invalid signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid request")
    # Debug
    # print("WEBHOOK:", body.decode('utf-8'))
    try:

        data  = json.loads(body.decode('utf-8'))
        keycloak_id = data.get("authDetails").get("userId")
        username = data.get("authDetails").get("username")
        email = get_email_by_id(keycloak_id)
        credits = 0

    except Exception as e:
        #print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

    try:
        # Get database session properly using context manager
        db = next(get_db())
        try:
            # Check if user already exists first (before creating User object)
            existing_user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
            if existing_user:
                return "{'response': 'User already exists in database'}"
            
            # Create new user only if it doesn't exist
            user = User(
                keycloak_id=keycloak_id,
                username=username,
                email=email,
                credits=credits
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return "{'response': 'User added to database'}"
            
        finally:
            db.close()
        
    except Exception as e:
        #print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return "{'response': 'User added to database'}"

@router.get("/", dependencies=[Depends(check_admin_role)])
async def get_users():
    try:
        # Get database session properly using context manager
        db = next(get_db())
        try:
            users = db.query(User).all()
            return users
        finally:
            db.close()
    except Exception as e:
        #print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{user_id}", dependencies=[Depends(check_admin_role)])
async def get_user(user_id: int):
    try:
        # Get database session properly using context manager
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        finally:
            db.close()
    except Exception as e:
        #print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")