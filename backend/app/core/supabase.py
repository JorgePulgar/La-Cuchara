"""
backend/app/core/supabase.py
Initializes the Supabase client using environment variables.
Handles missing env vars gracefully — does not crash on startup.
"""

from supabase import create_client, Client
from app.core.config import settings


# TODO: conectar Supabase
_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """
    Returns the Supabase client singleton.
    Raises RuntimeError if environment variables are not configured.
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise RuntimeError(
            "Supabase not connected: check environment variables. "
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set in backend/.env"
        )

    try:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,
        )
        return _supabase_client
    except Exception as e:
        raise RuntimeError(
            f"Supabase not connected: failed to create client. Error: {e}"
        )


def get_supabase_admin_client() -> Client:
    """
    Returns a Supabase client using the service role key (admin access).
    Used for server-side operations that bypass RLS.
    Raises RuntimeError if environment variables are not configured.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "Supabase not connected: check environment variables. "
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in backend/.env"
        )

    try:
        return create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    except Exception as e:
        raise RuntimeError(
            f"Supabase not connected: failed to create admin client. Error: {e}"
        )
