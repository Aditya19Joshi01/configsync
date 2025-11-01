from fastapi import Request, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

# Define a header name (e.g., x-api-key)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

async def verify_api_key(request: Request, api_key: str = Security(api_key_header)):
    """
    Dependency to verify that the correct API key is present in request headers.
    """
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key
