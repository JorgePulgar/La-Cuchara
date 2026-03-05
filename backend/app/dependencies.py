"""
backend/app/dependencies.py
FastAPI dependency injection functions.
Provides get_current_user for JWT-based authentication via Supabase Auth.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.supabase import get_supabase_client

# HTTP Bearer token extractor
security = HTTPBearer()


# TODO: conectar Supabase
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Extracts and verifies the JWT from the Authorization header
    via Supabase Auth. Returns the authenticated user data.

    Returns 401 if the token is invalid or expired.
    Returns 500 if Supabase is not connected.
    """
    token = credentials.credentials

    try:
        supabase = get_supabase_client()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    try:
        # Verify the JWT and get the user
        user_response = supabase.auth.get_user(token)

        if user_response is None or user_response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Fetch user profile from the users table
        user_data = (
            supabase.table("users")
            .select("*")
            .eq("id", str(user_response.user.id))
            .single()
            .execute()
        )

        if user_data.data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found in database",
            )

        return user_data.data

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
