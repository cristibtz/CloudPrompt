import hashlib
import hmac
from fastapi import HTTPException, Header, APIRouter, Request, Depends
from dotenv import load_dotenv
import os, json
from typing import Dict

from app.utils.get_email_by_id import get_email_by_id
from app.utils.check_admin_role import check_admin_role
from app.models.responses import StandardResponse, ErrorDetail
from app.auth import auth

from app.database.db import get_db
from app.models.user import User
from app.models.prompts import Prompt
from app.models.credentials import Credential

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../','.env'))

router = APIRouter()

@router.post("/keycloak-webhook", 
             tags=["User Management"], 
             response_model=Dict,
             summary="Keycloak webhook handler",
             description="Handle user creation/update events from Keycloak authentication service",
             responses={
                 200: {
                     "description": "Webhook processed successfully",
                     "content": {
                         "application/json": {
                             "example": {
                                 "success": True,
                                 "message": "User created successfully"
                             }
                         }
                     }
                 },
                 401: {
                     "description": "Invalid webhook signature",
                     "content": {
                         "application/json": {
                             "example": {
                                 "success": False,
                                 "error": {
                                     "code": "INVALID_SIGNATURE",
                                     "message": "Authentication failed"
                                 }
                             }
                         }
                     }
                 },
                 500: {
                     "description": "Internal server error",
                     "content": {
                         "application/json": {
                             "example": {
                                 "success": False,
                                 "error": {
                                     "code": "INTERNAL_ERROR",
                                     "message": "Failed to process webhook"
                                 }
                             }
                         }
                     }
                 }
             })
async def webhook_handler(
    request: Request,
    x_keycloak_signature: str = Header(None, alias="X-Keycloak-Signature")
):
    """
    Handle Keycloak webhook events.
    
    Processes user creation and update events from the Keycloak authentication service.
    Validates webhook signature for security and creates/updates local user records.
    
    Args:
        request: HTTP request containing webhook payload
        x_keycloak_signature: Webhook signature for validation
    
    Returns:
        Dict: Success or error response
        
    Raises:
        HTTPException: For invalid signatures or processing errors
    """
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
                raise HTTPException(
                    status_code=401, 
                    detail={
                        "success": False,
                        "error": {
                            "code": "INVALID_SIGNATURE",
                            "message": "Authentication failed"
                        }
                    }
                )
    except Exception:
        raise HTTPException(
            status_code=400, 
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Invalid webhook request"
                }
            }
        )
    
    try:
        data = json.loads(body.decode('utf-8'))
        keycloak_id = data.get("authDetails").get("userId")
        username = data.get("authDetails").get("username")
        email = get_email_by_id(keycloak_id)
        credits = 0

    except Exception:
        raise HTTPException(
            status_code=500, 
            detail={
                "success": False,
                "error": {
                    "code": "WEBHOOK_PROCESSING_ERROR",
                    "message": "Failed to process webhook data"
                }
            }
        )

    try:
        db = next(get_db())
        try:
            existing_user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
            if existing_user:
                return {
                    "success": True,
                    "message": "User already exists",
                    "data": {
                        "user_id": existing_user.id,
                        "action": "skipped"
                    }
                }
            
            user = User(
                keycloak_id=keycloak_id,
                username=username,
                email=email,
                credits=credits
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return {
                "success": True,
                "message": "User created successfully",
                "data": {
                    "user_id": user.id,
                    "username": user.username,
                    "action": "created"
                }
            }
            
        finally:
            db.close()
        
    except Exception:
        raise HTTPException(
            status_code=500, 
            detail={
                "success": False,
                "error": {
                    "code": "USER_CREATION_FAILED",
                    "message": "Failed to process user"
                }
            }
        )

@router.get("/", 
            dependencies=[Depends(check_admin_role)], 
            response_model=Dict, 
            tags=["User Management"],
            summary="Get all users (Admin only)",
            description="Retrieve all registered users in the system. Requires admin privileges.",
            responses={
                200: {
                    "description": "Users retrieved successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "success": True,
                                "data": [
                                    {
                                        "id": 1,
                                        "username": "john_doe",
                                        "email": "john@example.com",
                                        "keycloak_id": "123e4567-e89b-12d3-a456-426614174000",
                                        "credits": 100
                                    }
                                ],
                                "message": "Users retrieved successfully"
                            }
                        }
                    }
                },
                403: {
                    "description": "Forbidden - Admin access required"
                },
                500: {
                    "description": "Internal server error",
                    "content": {
                        "application/json": {
                            "example": {
                                "success": False,
                                "error": {
                                    "code": "INTERNAL_ERROR",
                                    "message": "Failed to retrieve users"
                                }
                            }
                        }
                    }
                }
            })
async def get_users():
    """
    Get all users (Admin only).
    
    Retrieves all registered users in the system with their basic information.
    This endpoint is restricted to users with admin privileges.
    
    Returns:
        Dict: List of all users with their details
    """
    try:
        db = next(get_db())
        try:
            users = db.query(User).all()
            return {
                "success": True,
                "data": [
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "keycloak_id": user.keycloak_id,
                        "credits": user.credits
                    } for user in users
                ],
                "message": "Users retrieved successfully"
            }
        finally:
            db.close()
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{user_id}", 
            dependencies=[Depends(check_admin_role)], 
            response_model=Dict, 
            tags=["User Management"],
            summary="Get specific user (Admin only)",
            description="Retrieve details for a specific user by ID. Requires admin privileges.",
            responses={
                200: {
                    "description": "User retrieved successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "success": True,
                                "data": {
                                    "id": 1,
                                    "username": "john_doe",
                                    "email": "john@example.com",
                                    "keycloak_id": "123e4567-e89b-12d3-a456-426614174000",
                                    "credits": 100
                                },
                                "message": "User retrieved successfully"
                            }
                        }
                    }
                },
                404: {
                    "description": "User not found",
                    "content": {
                        "application/json": {
                            "example": {
                                "success": False,
                                "error": {
                                    "code": "NOT_FOUND",
                                    "message": "User not found"
                                }
                            }
                        }
                    }
                },
                403: {
                    "description": "Forbidden - Admin access required"
                },
                500: {
                    "description": "Internal server error",
                    "content": {
                        "application/json": {
                            "example": {
                                "success": False,
                                "error": {
                                    "code": "INTERNAL_ERROR",
                                    "message": "Failed to retrieve user"
                                }
                            }
                        }
                    }
                }
            })
async def get_user(user_id: int):
    """
    Get specific user (Admin only).
    
    Retrieves detailed information for a specific user by their ID.
    This endpoint is restricted to users with admin privileges.
    
    Args:
        user_id: The ID of the user to retrieve
    
    Returns:
        Dict: User details including username, email, and credits
        
    Raises:
        HTTPException: If user not found or access denied
    """
    try:
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return {
                "success": True,
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "keycloak_id": user.keycloak_id,
                    "credits": user.credits
                },
                "message": "User retrieved successfully"
            }
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")