import hashlib
import hmac
from fastapi import HTTPException, Header, APIRouter, Request, Depends
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../','.env'))

router = APIRouter()

allowed_hosts = ["192.168.100.11", "127.0.0.1"]

@router.post("/keycloak-webhook", tags=["users"])
async def webhook_handler(
    request: Request,
    x_keycloak_signature: str = Header(None, alias="X-Keycloak-Signature")
):
    body = await request.body()
    client_host = request.client.host

    if client_host not in allowed_hosts:
        raise HTTPException(status_code=403, detail="Forbidden")

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
    
    print("WEBHOOK:", body.decode('utf-8'))
    return {"ok": True}