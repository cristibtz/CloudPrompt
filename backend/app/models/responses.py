from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union

class ErrorDetail(BaseModel):
    """Error details for failed operations."""
    code: str = Field(..., description="Machine-readable error code", example="INVALID_INPUT")
    message: str = Field(..., description="Human-readable error message", example="The provided input is invalid")

class StandardResponse(BaseModel):
    """Standard API response format used across all endpoints."""
    success: bool = Field(..., description="Indicates if the operation was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data (present on success)")
    message: Optional[str] = Field(None, description="Success message", example="Operation completed successfully")
    error: Optional[ErrorDetail] = Field(None, description="Error details (present on failure)")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "data": {"id": 1, "name": "example"},
                    "message": "Operation successful"
                },
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Required field is missing"
                    }
                }
            ]
        }

class ExecuteResponse(BaseModel):
    """Response format for command execution operations."""
    success: bool = Field(..., description="Indicates if the command execution was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Command execution results")
    provider: Optional[str] = Field(None, description="Cloud provider used for execution", example="aws")
    message: Optional[str] = Field(None, description="Execution status message", example="Prompt executed successfully")
    error: Optional[ErrorDetail] = Field(None, description="Error details if execution failed")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "data": {"instances": [{"id": "i-123", "state": "running"}]},
                    "provider": "aws",
                    "message": "Prompt executed successfully"
                },
                {
                    "success": False,
                    "error": {
                        "code": "EXECUTION_FAILED",
                        "message": "Prompt execution failed"
                    }
                }
            ]
        }

class CredentialResponse(BaseModel):
    """Response format for credential management operations."""
    success: bool = Field(..., description="Indicates if the credential operation was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Credential data (without sensitive information)")
    message: Optional[str] = Field(None, description="Operation status message", example="Credential created successfully")
    error: Optional[ErrorDetail] = Field(None, description="Error details if operation failed")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "data": {"id": 1, "name": "aws-prod", "provider": "aws"},
                    "message": "Credential created successfully"
                },
                {
                    "success": False,
                    "error": {
                        "code": "CREDENTIAL_EXISTS",
                        "message": "A credential with this name already exists"
                    }
                }
            ]
        }
