"""
backend/app/routers/restaurants.py
Restaurant endpoints: nearby restaurants, today's menu, and filtered discovery.
"""

from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.core.supabase import get_supabase_client
from app.models.schemas import (
    MenuWithItemsOut,
    RestaurantNearbyOut,
)

router = APIRouter()


# TODO: conectar Supabase


@router.get("/nearby", response_model=list[RestaurantNearbyOut])
async def get_nearby_restaurants(
    lat: float = Query(..., description="User's latitude"),
    lon: float = Query(..., description="User's longitude"),
    radius_km: float = Query(5.0, ge=0.1, le=100, description="Search radius in km"),
    min_rating: float | None = Query(None, ge=1, le=5, description="Minimum average rating"),
    has_menu_today: bool = Query(False, description="Only return restaurants with a menu for today"),
):
    """
    GET /restaurants/nearby
    Returns restaurants within a given radius, ordered by distance.
    Optionally filters by minimum rating and/or having a menu for today.
    Uses a PostgreSQL function with the Haversine formula via Supabase RPC.
    """
    try:
        supabase = get_supabase_client()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase not connected: {e}",
        )

    # 1. Get nearby restaurants via RPC (Haversine function)
    try:
        rpc_result = supabase.rpc(
            "get_nearby_restaurants",
            {"user_lat": lat, "user_lon": lon, "radius_km": radius_km},
        ).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch nearby restaurants: {e}",
        )

    restaurants = rpc_result.data or []

    # 2. Compute average rating for each restaurant (from ratings → menu_items → menus)
    results: list[dict] = []
    for r in restaurants:
        restaurant_id = r["id"]
        average_rating = None

        try:
            # Get all menus for this restaurant
            menus_result = (
                supabase.table("menus")
                .select("id")
                .eq("restaurant_id", restaurant_id)
                .execute()
            )
            menu_ids = [m["id"] for m in (menus_result.data or [])]

            if menu_ids:
                # Get all menu_item ids for those menus
                items_result = (
                    supabase.table("menu_items")
                    .select("id")
                    .in_("menu_id", menu_ids)
                    .execute()
                )
                item_ids = [item["id"] for item in (items_result.data or [])]

                if item_ids:
                    # Get average rating from ratings table
                    ratings_result = (
                        supabase.table("ratings")
                        .select("rating")
                        .in_("menu_item_id", item_ids)
                        .execute()
                    )
                    ratings = ratings_result.data or []
                    if ratings:
                        total = sum(rt["rating"] for rt in ratings)
                        average_rating = round(total / len(ratings), 2)
        except Exception:
            # If ratings fail, just skip — not critical
            pass

        # 3. Filter by min_rating if specified
        if min_rating is not None and (average_rating is None or average_rating < min_rating):
            continue

        # 4. Filter by has_menu_today if specified
        if has_menu_today:
            try:
                today_str = date.today().isoformat()
                menu_today = (
                    supabase.table("menus")
                    .select("id")
                    .eq("restaurant_id", restaurant_id)
                    .eq("date", today_str)
                    .limit(1)
                    .execute()
                )
                if not menu_today.data:
                    continue
            except Exception:
                continue

        results.append({
            **r,
            "average_rating": average_rating,
        })

    return results


@router.get("/{restaurant_id}/menu/today", response_model=MenuWithItemsOut)
async def get_today_menu(restaurant_id: str):
    """
    GET /restaurants/{restaurant_id}/menu/today
    Fetches the menu for today and all its menu items.
    Returns 404 if no menu exists for today.
    """
    try:
        supabase = get_supabase_client()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase not connected: {e}",
        )

    today_str = date.today().isoformat()

    # 1. Fetch today's menu
    try:
        menu_result = (
            supabase.table("menus")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .eq("date", today_str)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch menu: {e}",
        )

    if not menu_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No menu available for today",
        )

    menu = menu_result.data[0]

    # 2. Fetch menu items
    try:
        items_result = (
            supabase.table("menu_items")
            .select("*")
            .eq("menu_id", menu["id"])
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch menu items: {e}",
        )

    menu["items"] = items_result.data or []

    return menu
