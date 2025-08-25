from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi import Depends, HTTPException

import jwt
from jwt import PyJWKClient
from typing import Annotated

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../','.env'))

oauth_2_scheme = OAuth2AuthorizationCodeBearer(
    tokenUrl=f"{os.getenv('KEYCLOAK_SERVER_URL')}/realms/cloudprompt/protocol/openid-connect/token",
    authorizationUrl=f"{os.getenv('KEYCLOAK_SERVER_URL')}/realms/cloudprompt/protocol/openid-connect/auth",
    refreshUrl=f"{os.getenv('KEYCLOAK_SERVER_URL')}/realms/cloudprompt/protocol/openid-connect/token",
)


async def valid_access_token(
    access_token: Annotated[str, Depends(oauth_2_scheme)]
):
    url = f"{os.getenv("KEYCLOAK_SERVER_URL")}/realms/cloudprompt/protocol/openid-connect/certs"
    jwks_client = PyJWKClient(url)

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(access_token)
        data = jwt.decode(
            access_token,
            signing_key.key,
            algorithms=["RS256"],
            audience="cloudprompt-client",
            options={"verify_exp": True},
        )
        print("Token is valid. Claims:", data)
        return data
    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Not authenticated")
