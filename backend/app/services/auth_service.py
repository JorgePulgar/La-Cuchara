"""
backend/app/services/auth_service.py
Business logic for authentication (signup, login, logout, get user profile).
All Supabase calls are wrapped in try/except with descriptive errors.
"""

from uuid import UUID

from app.core.supabase import get_supabase_client, get_supabase_admin_client
from app.models.schemas import TokenResponse
from app.services.geocoding_service import geocode_address


# TODO: conectar Supabase


async def signup_user(
    email: str,
    password: str,
    role: str,
    restaurant_name: str | None = None,
    restaurant_address: str | None = None,
    restaurant_phone: str | None = None,
) -> TokenResponse:
    """
    Creates a new user in Supabase Auth, inserts a row in the users table,
    and optionally creates a restaurant if role is 'owner'.

    Returns a TokenResponse with access_token, user_id, email, and role.
    """
    try:
        supabase = get_supabase_client()
    except RuntimeError as e:
        raise RuntimeError(f"Supabase not connected: {e}")

    # 1. Create user in Supabase Auth
    try:
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password,
        })
    except Exception as e:
        raise RuntimeError(f"Failed to create user in Supabase Auth: {e}")

    if auth_response.user is None:
        raise RuntimeError("Supabase Auth returned no user. Signup may have failed.")

    user_id = str(auth_response.user.id)
    access_token = auth_response.session.access_token if auth_response.session else ""

    # 2. Insert row in users table FIRST (without restaurant_id) to satisfy FK constraints
    try:
        user_row = {
            "id": user_id,
            "email": email,
            "role": role,
            "restaurant_id": None,
        }
        supabase.table("users").insert(user_row).execute()
    except Exception as e:
        raise RuntimeError(f"Failed to insert user profile: {e}")

    # 3. If role is 'owner', create the restaurant and update the user
    if role == "owner":
        if not restaurant_name:
            raise ValueError("restaurant_name is required when role is 'owner'")
        if not restaurant_address:
            raise ValueError("restaurant_address is required when role is 'owner'")
        if not restaurant_phone:
            raise ValueError("restaurant_phone is required when role is 'owner'")

        # Geocode the address to get lat/lon
        lat, lon = await geocode_address(restaurant_address)

        try:
            restaurant_data = {
                "name": restaurant_name,
                "address": restaurant_address,
                "phone": restaurant_phone,
                "lat": lat,
                "lon": lon,
                "owner_user_id": user_id,
            }
            restaurant_result = (
                supabase.table("restaurants")
                .insert(restaurant_data)
                .execute()
            )
            
            if restaurant_result.data:
                restaurant_id = restaurant_result.data[0]["id"]
                # Update user with the new restaurant_id
                supabase.table("users").update({"restaurant_id": restaurant_id}).eq("id", user_id).execute()
        except Exception as e:
            # If restaurant creation fails, we might want to log it, but the user is already created.
            raise RuntimeError(f"Failed to create restaurant: {e}")

    return TokenResponse(
        access_token=access_token,
        user_id=UUID(user_id),
        email=email,
        role=role,
    )


async def login_user(email: str, password: str) -> TokenResponse:
    """
    Authenticates a user via Supabase Auth.
    Returns a TokenResponse with access_token, user_id, and role.
    """
    try:
        supabase = get_supabase_client()
    except RuntimeError as e:
        raise RuntimeError(f"Supabase not connected: {e}")

    # 1. Sign in with Supabase Auth
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
    except Exception as e:
        raise RuntimeError(f"Login failed: {e}")

    if auth_response.user is None or auth_response.session is None:
        raise RuntimeError("Invalid email or password")

    user_id = str(auth_response.user.id)
    access_token = auth_response.session.access_token

    # 2. Fetch role from users table
    try:
        user_data = (
            supabase.table("users")
            .select("role")
            .eq("id", user_id)
            .single()
            .execute()
        )
        role = user_data.data["role"] if user_data.data else "user"
    except Exception:
        role = "user"

    return TokenResponse(
        access_token=access_token,
        user_id=UUID(user_id),
        email=email,
        role=role,
    )


async def logout_user(token: str) -> dict:
    """
    Invalidates the user's session in Supabase Auth.
    """
    try:
        supabase = get_supabase_client()
    except RuntimeError as e:
        raise RuntimeError(f"Supabase not connected: {e}")

    try:
        supabase.auth.sign_out(token)
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise RuntimeError(f"Logout failed: {e}")
