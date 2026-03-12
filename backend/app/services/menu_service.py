"""
backend/app/services/menu_service.py
Persistence logic for corrected menu analysis results.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.core.supabase import get_supabase_admin_client


async def save_corrected_menu(
    current_user: dict,
    menu_date: date,
    season_tag: str | None,
    fields: dict[str, Any],
    items: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Persists a corrected menu and its menu items in Supabase.

    The restaurant is derived from the authenticated owner/admin user.
    """
    restaurant_id = current_user.get("restaurant_id")
    if not restaurant_id:
        raise ValueError("The authenticated user is not linked to any restaurant")

    cleaned_items = [item.strip() for item in items if item.strip()]
    parsed_json = {
        **fields,
        "MenuItems": cleaned_items,
    }

    supabase = get_supabase_admin_client()

    menu_payload = {
        "restaurant_id": restaurant_id,
        "date": menu_date.isoformat(),
        "source_image_id": None,
        "raw_text": "\n".join(cleaned_items) if cleaned_items else None,
        "parsed_json": parsed_json,
        "season_tag": season_tag.strip() if season_tag else None,
    }

    try:
        menu_response = (
            supabase.table("menus")
            .insert(menu_payload)
            .execute()
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to save menu: {exc}") from exc

    menu_data = menu_response.data[0] if menu_response.data else None
    if menu_data is None:
        raise RuntimeError("Menu insert succeeded but no menu data was returned")

    menu_items_data: list[dict[str, Any]] = []
    if cleaned_items:
        item_payloads = [
            {
                "menu_id": menu_data["id"],
                "name": item_name,
                "description": None,
                "price": None,
                "tags": None,
                "predicted": False,
            }
            for item_name in cleaned_items
        ]

        try:
            items_response = (
                supabase.table("menu_items")
                .insert(item_payloads)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to save menu items: {exc}") from exc

        menu_items_data = items_response.data or []

    return menu_data, menu_items_data