"""
backend/app/routers/auth.py
Auth endpoints: signup, login, logout, and get current user profile.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.dependencies import get_current_user
from app.models.schemas import (
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UserOut,
)
from app.services.auth_service import login_user, logout_user, signup_user

router = APIRouter()
security = HTTPBearer()


# TODO: conectar Supabase


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest):
    """
    POST /auth/signup
    Creates a new user in Supabase Auth and the users table.
    If role is 'owner', also creates a restaurant.
    Returns access_token, user_id, email, and role.
    """
    # Validate: owner must provide restaurant details
    if request.role == "owner":
        if not request.restaurant_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="restaurant_name is required when role is 'owner'",
            )
        if not request.restaurant_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="restaurant_address is required when role is 'owner'",
            )
        if not request.restaurant_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="restaurant_phone is required when role is 'owner'",
            )

    try:
        result = await signup_user(
            email=request.email,
            password=request.password,
            role=request.role,
            restaurant_name=request.restaurant_name,
            restaurant_address=request.restaurant_address,
            restaurant_phone=request.restaurant_phone,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    POST /auth/login
    Authenticates a user via Supabase Auth.
    Returns access_token, user_id, and role.
    """
    try:
        result = await login_user(
            email=request.email,
            password=request.password,
        )
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    POST /auth/logout
    Invalidates the current session in Supabase Auth.
    """
    try:
        result = await logout_user(token=credentials.credentials)
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    GET /auth/me
    Returns the authenticated user's profile from the users table.
    """
    return current_user
