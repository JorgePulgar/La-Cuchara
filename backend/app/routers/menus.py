"""
backend/app/routers/menus.py
Menu endpoints for persisting corrected analyzed menus and searching menu items.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_user
from app.core.supabase import get_supabase_client
from app.models.schemas import MenuItemSearchOut, SaveMenuRequest, SaveMenuResponse

router = APIRouter()


@router.post("", response_model=SaveMenuResponse, status_code=status.HTTP_201_CREATED)
async def create_menu(
	request: SaveMenuRequest,
	current_user: dict = Depends(get_current_user),
):
	"""
	Persists a corrected menu and its corrected menu items.

	The target restaurant is derived from the authenticated owner/admin user.
	"""
	if current_user.get("role") not in {"owner", "admin"}:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Only owners and admins can save menus",
		)

	try:
		from app.services.menu_service import save_corrected_menu

		menu_data, menu_items_data = await save_corrected_menu(
			current_user=current_user,
			menu_date=request.date,
			season_tag=request.season_tag,
			fields=request.fields,
			items=request.items,
		)
		return {
			"menu": menu_data,
			"menu_items": menu_items_data,
		}
	except ValueError as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(exc),
		) from exc
	except RuntimeError as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=str(exc),
		) from exc


# TODO: conectar Supabase


@router.get("/search", response_model=list[MenuItemSearchOut])
async def search_menu_items(
    q: str = Query(..., min_length=1, description="Search term"),
    lat: float = Query(..., description="User's latitude"),
    lon: float = Query(..., description="User's longitude"),
    radius_km: float = Query(5.0, ge=0.1, le=100, description="Search radius in km"),
):
    """
    GET /menu-items/search
    Searches menu items by name or description (case-insensitive partial match).
    Only returns items from restaurants within the given radius.
    """
    try:
        supabase = get_supabase_client()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase not connected: {e}",
        )

    # 1. Get nearby restaurant IDs via RPC
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

    nearby_restaurants = rpc_result.data or []
    if not nearby_restaurants:
        return []

    # Build a lookup: restaurant_id -> restaurant_name
    restaurant_lookup = {r["id"]: r["name"] for r in nearby_restaurants}
    restaurant_ids = list(restaurant_lookup.keys())

    # 2. Get menus belonging to these restaurants
    try:
        menus_result = (
            supabase.table("menus")
            .select("id, restaurant_id")
            .in_("restaurant_id", restaurant_ids)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch menus: {e}",
        )

    menus = menus_result.data or []
    if not menus:
        return []

    # Build lookup: menu_id -> restaurant_id
    menu_to_restaurant = {m["id"]: m["restaurant_id"] for m in menus}
    menu_ids = list(menu_to_restaurant.keys())

    # 3. Search menu items by name or description (ilike)
    search_pattern = f"%{q}%"
    try:
        # Search by name
        name_result = (
            supabase.table("menu_items")
            .select("*")
            .in_("menu_id", menu_ids)
            .ilike("name", search_pattern)
            .execute()
        )
        # Search by description
        desc_result = (
            supabase.table("menu_items")
            .select("*")
            .in_("menu_id", menu_ids)
            .ilike("description", search_pattern)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search menu items: {e}",
        )

    # Merge results, deduplicate by id
    seen_ids = set()
    results: list[dict] = []

    for item in (name_result.data or []) + (desc_result.data or []):
        if item["id"] in seen_ids:
            continue
        seen_ids.add(item["id"])

        restaurant_id = menu_to_restaurant.get(item["menu_id"])
        restaurant_name = restaurant_lookup.get(restaurant_id, "Unknown")

        results.append({
            **item,
            "restaurant_id": restaurant_id,
            "restaurant_name": restaurant_name,
        })

    return results
