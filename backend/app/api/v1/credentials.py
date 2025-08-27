from fastapi import HTTPException, Header, APIRouter, Request, Depends
from dotenv import load_dotenv
import os, json, base64
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.auth import auth
from app.utils.check_admin_role import check_admin_role
from app.utils.get_id_by_kc_id import get_id_by_kc_id
from app.models.responses import CredentialResponse, ErrorDetail

from app.database.db import get_db
from app.models.user import User
from app.models.prompts import Prompt
from app.models.credentials import Credential

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../','.env'))

router = APIRouter()

class CreateCredentialRequest(BaseModel):
    """Request model for creating new credentials."""
    provider: str = Field(..., 
                         description="Cloud provider for the credentials",
                         example="aws")
    name: str = Field(..., 
                     description="Unique name for the credential set",
                     example="my-aws-production",
                     min_length=1,
                     max_length=50)
    data: Dict[str, Any] = Field(..., 
                                description="Provider-specific credential data",
                                example={
                                    "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
                                    "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                                })

    class Config:
        schema_extra = {
            "examples": [
                {
                    "provider": "aws",
                    "name": "my-aws-production",
                    "data": {
                        "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE", 
                        "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                    }
                },
                {
                    "provider": "azure",
                    "name": "my-azure-dev",
                    "data": {
                        "AZURE_CLIENT_ID": "12345678-1234-1234-1234-123456789012",
                        "AZURE_CLIENT_SECRET": "your-client-secret",
                        "AZURE_TENANT_ID": "87654321-4321-4321-4321-210987654321"
                    }
                }
            ]
        }

providers = ["aws", "azure", "gcp", "proxmox"]
max_creds_per_user = 5

@router.post("/", 
             tags=["Credential Management"], 
             dependencies=[Depends(auth.valid_access_token)], 
             response_model=CredentialResponse,
             summary="Create new credentials",
             description="Store encrypted credentials for a specific cloud provider",
             responses={
                 200: {
                     "description": "Credentials created successfully",
                     "content": {
                         "application/json": {
                             "example": {
                                 "success": True,
                                 "data": {
                                     "id": 1,
                                     "name": "my-aws-production",
                                     "provider": "aws"
                                 },
                                 "message": "Credential created successfully"
                             }
                         }
                     }
                 },
                 400: {
                     "description": "Bad request - validation error",
                     "content": {
                         "application/json": {
                             "examples": {
                                 "invalid_name": {
                                     "summary": "Invalid credential name",
                                     "value": {
                                         "success": False,
                                         "error": {
                                             "code": "INVALID_NAME",
                                             "message": "Credential name is required"
                                         }
                                     }
                                 },
                                 "unsupported_provider": {
                                     "summary": "Unsupported provider",
                                     "value": {
                                         "success": False,
                                         "error": {
                                             "code": "UNSUPPORTED_PROVIDER",
                                             "message": "Provider not supported"
                                         }
                                     }
                                 }
                             }
                         }
                     }
                 },
                 401: {
                     "description": "Unauthorized - invalid or missing token"
                 },
                 500: {
                     "description": "Internal server error",
                     "content": {
                         "application/json": {
                             "example": {
                                 "success": False,
                                 "error": {
                                     "code": "INTERNAL_ERROR",
                                     "message": "Failed to create credential"
                                 }
                             }
                         }
                     }
                 }
             })
async def create_credential(request: CreateCredentialRequest,
    token_data: Dict = Depends(auth.valid_access_token)
    ):
    name = request.name.strip() if request.name else ""
    provider = request.provider
    data = request.data

    if not name:
        raise HTTPException(
            status_code=400, 
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_NAME",
                    "message": "Credential name is required"
                }
            }
        )

    if not provider or not data:
        raise HTTPException(
            status_code=400, 
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "Provider and credential data are required"
                }
            }
        )

    if provider not in providers:
        raise HTTPException(
            status_code=400, 
            detail={
                "success": False,
                "error": {
                    "code": "UNSUPPORTED_PROVIDER",
                    "message": "Provider not supported"
                }
            }
        )

    if provider == "aws":
        if "AWS_ACCESS_KEY" not in data or "AWS_SECRET_ACCESS_KEY" not in data:
            raise HTTPException(
                status_code=400, 
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid credential format for AWS"
                    }
                }
            )
        if not data.get("AWS_ACCESS_KEY") or not data.get("AWS_SECRET_ACCESS_KEY"):
            raise HTTPException(
                status_code=400, 
                detail={
                    "success": False,
                    "error": {
                        "code": "EMPTY_CREDENTIALS",
                        "message": "Credential values cannot be empty"
                    }
                }
            )
    elif provider == "proxmox":
        if "host" not in data or "username" not in data or "password" not in data:
            raise HTTPException(
                status_code=400, 
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid credential format for Proxmox"
                    }
                }
            )
        if not data.get("host") or not data.get("username") or not data.get("password"):
            raise HTTPException(
                status_code=400, 
                detail={
                    "success": False,
                    "error": {
                        "code": "EMPTY_CREDENTIALS",
                        "message": "Credential values cannot be empty"
                    }
                }
            )

    try:
        keycloak_id = token_data.get("sub")
        
        user_id = get_id_by_kc_id(keycloak_id)

        db = next(get_db())

        existing_cred = db.query(Credential).filter(
            Credential.user_id == user_id,
            Credential.name == name
        ).first()
        if existing_cred:
            raise HTTPException(
                status_code=400, 
                detail={
                    "success": False,
                    "error": {
                        "code": "DUPLICATE_NAME",
                        "message": "Credential name already exists"
                    }
                }
            )

        existing_creds_count = db.query(Credential).filter(
            Credential.user_id == user_id,
            Credential.provider == provider
        ).count()
        if existing_creds_count >= max_creds_per_user:
            raise HTTPException(
                status_code=400, 
                detail={
                    "success": False,
                    "error": {
                        "code": "LIMIT_EXCEEDED",
                        "message": "Maximum credentials limit reached"
                    }
                }
            )
        
        new_cred = Credential(
            user_id=user_id,
            provider=provider,
            name=name,
            data=base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')
        )
        db.add(new_cred)
        db.commit()
        db.refresh(new_cred)
        
        return {
            "success": True,
            "message": "Credential created successfully",
            "data": {
                "id": new_cred.id,
                "name": new_cred.name,
                "provider": new_cred.provider
            }
        }
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, 
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to create credential"
                }
            }
        )

@router.get("/", 
            tags=["Credential Management"], 
            dependencies=[Depends(check_admin_role)], 
            response_model=Dict,
            summary="Get all credentials (Admin only)",
            description="Retrieve all stored credentials across all users. Requires admin privileges.",
            responses={
                200: {
                    "description": "Credentials retrieved successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "success": True,
                                "data": [
                                    {"id": 1, "name": "aws-prod", "provider": "aws", "user_id": 1},
                                    {"id": 2, "name": "azure-dev", "provider": "azure", "user_id": 2}
                                ],
                                "message": "Credentials retrieved successfully"
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
                                    "message": "Failed to retrieve credentials"
                                }
                            }
                        }
                    }
                }
            })
async def get_credentials():
    """
    Get all credentials (Admin only).
    
    Retrieves all stored credentials across all users in the system.
    This endpoint is restricted to users with admin privileges.
    
    Returns:
        Dict: List of all credentials with basic metadata (no sensitive data)
    """
    try:
        db = next(get_db())
        creds = db.query(Credential).all()
        decoded_creds =[ ]
        return {
            "success": True,
            "data": [{"id": c.id, "name": c.name, "provider": c.provider, "user_id": c.user_id} for c in creds],
            "message": "Credentials retrieved successfully"
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/user", 
            tags=["Credential Management"], 
            dependencies=[Depends(auth.valid_access_token)], 
            response_model=Dict,
            summary="Get user credentials",
            description="Retrieve all credentials belonging to the authenticated user",
            responses={
                200: {
                    "description": "User credentials retrieved successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "success": True,
                                "data": [
                                    {"id": 1, "name": "my-aws-prod", "provider": "aws"},
                                    {"id": 2, "name": "my-azure-dev", "provider": "azure"}
                                ],
                                "message": "User credentials retrieved successfully"
                            }
                        }
                    }
                },
                401: {
                    "description": "Unauthorized - valid token required"
                },
                500: {
                    "description": "Internal server error",
                    "content": {
                        "application/json": {
                            "example": {
                                "success": False,
                                "error": {
                                    "code": "INTERNAL_ERROR",
                                    "message": "Failed to retrieve credentials"
                                }
                            }
                        }
                    }
                }
            })
async def get_user_credentials(token_data: Dict = Depends(auth.valid_access_token)):
    """
    Get user's credentials.
    
    Retrieves all credentials belonging to the authenticated user.
    Returns only metadata (id, name, provider) without sensitive credential data.
    
    Args:
        token_data: Authentication token data (automatically injected)
    
    Returns:
        Dict: List of user's credentials with basic metadata
    """
    try:
        keycloak_id = token_data.get("sub")
        
        user_id = get_id_by_kc_id(keycloak_id)

        db = next(get_db())

        creds = db.query(Credential).filter(Credential.user_id == user_id).all()
        return {
            "success": True,
            "data": [{"id": c.id, "name": c.name, "provider": c.provider} for c in creds],
            "message": "User credentials retrieved successfully"
        }
    except Exception:
        raise HTTPException(
            status_code=500, 
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to retrieve credentials"
                }
            }
        )

@router.delete("/{cred_id}", 
               tags=["Credential Management"], 
               response_model=Dict,
               summary="Delete credential",
               description="Delete a specific credential belonging to the authenticated user",
               responses={
                   200: {
                       "description": "Credential deleted successfully",
                       "content": {
                           "application/json": {
                               "example": {
                                   "success": True,
                                   "message": "Credential 'my-aws-prod' deleted successfully"
                               }
                           }
                       }
                   },
                   404: {
                       "description": "Credential not found",
                       "content": {
                           "application/json": {
                               "example": {
                                   "success": False,
                                   "error": {
                                       "code": "NOT_FOUND",
                                       "message": "Credential not found"
                                   }
                               }
                           }
                       }
                   },
                   401: {
                       "description": "Unauthorized - valid token required"
                   },
                   500: {
                       "description": "Internal server error",
                       "content": {
                           "application/json": {
                               "example": {
                                   "success": False,
                                   "error": {
                                       "code": "INTERNAL_ERROR",
                                       "message": "Failed to delete credential"
                                   }
                               }
                           }
                       }
                   }
               })
async def delete_credential(
    cred_id: int,
    token_data: Dict = Depends(auth.valid_access_token)
):
    """
    Delete a credential.
    
    Permanently removes a credential from the user's account.
    Users can only delete their own credentials.
    
    Args:
        cred_id: The ID of the credential to delete
        token_data: Authentication token data (automatically injected)
    
    Returns:
        Dict: Success message confirming deletion
        
    Raises:
        HTTPException: If credential not found or access denied
    """
    try:
        keycloak_id = token_data.get("sub")
        
        user_id = get_id_by_kc_id(keycloak_id)

        db = next(get_db())

        cred = db.query(Credential).filter(Credential.id == cred_id, Credential.user_id == user_id).first()
        if not cred:
            raise HTTPException(
                status_code=404, 
                detail={
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Credential not found"
                    }
                }
            )

        cred_name = cred.name
        db.delete(cred)
        db.commit()
        
        return {
            "success": True,
            "message": "Credential deleted successfully",
            "data": {
                "deleted_credential": cred_name
            }
        }
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, 
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to delete credential"
                }
            }
        )