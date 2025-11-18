from pydantic import BaseModel
from typing import Optional, Any, Dict

class HealthCheck(BaseModel):
    status: str = "ok"
    message: str = "Service is healthy"

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None
