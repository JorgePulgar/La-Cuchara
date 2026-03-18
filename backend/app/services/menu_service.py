from __future__ import annotations

import json
from datetime import date
from typing import Any
from pathlib import Path

import pandas as pd

from app.core.supabase import get_supabase_admin_client

ML_DATA_DIR = Path(__file__).resolve().parents[1] / "ml" / "data"
RANKED_FILE = ML_DATA_DIR / "ranked_predictions.csv"


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


def infer_season_from_date(target_date: date) -> str:
    month = target_date.month

    if month in (12, 1, 2):
        return "invierno"
    if month in (3, 4, 5):
        return "primavera"
    if month in (6, 7, 8):
        return "verano"
    return "otono"


async def get_existing_weekly_prediction(
    restaurant_id: str,
    week_start_date: date,
) -> dict[str, Any] | None:
    supabase = get_supabase_admin_client()

    try:
        response = (
            supabase.table("predictions")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .eq("week_start_date", week_start_date.isoformat())
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch existing prediction: {exc}") from exc

    data = response.data or []
    return data[0] if data else None


async def get_menu_items_training_df_for_restaurant(
    restaurant_id: str,
) -> pd.DataFrame:
    supabase = get_supabase_admin_client()

    try:
        response = (
            supabase.table("menu_items_training")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .execute()
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch training data: {exc}") from exc

    data = response.data or []
    if not data:
        raise ValueError(
            f"No training data found in menu_items_training for restaurant_id={restaurant_id}"
        )

    df = pd.DataFrame(data)
    if df.empty:
        raise ValueError(
            f"Training dataframe is empty for restaurant_id={restaurant_id}"
        )

    return df


async def save_weekly_prediction(
    restaurant_id: str,
    week_start_date: date,
    predicted_menu_items: dict[str, Any],
    model_version: str,
) -> dict[str, Any]:
    supabase = get_supabase_admin_client()

    payload = {
        "restaurant_id": restaurant_id,
        "week_start_date": week_start_date.isoformat(),
        "predicted_menu_items": predicted_menu_items,
        "predicted_services": None,
        "model_version": model_version,
    }

    try:
        response = (
            supabase.table("predictions")
            .insert(payload)
            .execute()
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to save prediction: {exc}") from exc

    prediction_data = response.data[0] if response.data else None
    if prediction_data is None:
        raise RuntimeError("Prediction insert succeeded but no data was returned")

    return prediction_data


async def create_weekly_prediction(
    current_user: dict,
    week_start_date: date,
) -> dict[str, Any]:
    restaurant_id = current_user.get("restaurant_id")
    if not restaurant_id:
        raise ValueError("The authenticated user is not linked to any restaurant")

    if week_start_date.weekday() != 0:
        raise ValueError("week_start_date must be a Monday")

    restaurant_id = str(restaurant_id)

    # 1) Si ya existe, devolverla directamente
    existing_prediction = await get_existing_weekly_prediction(
        restaurant_id=restaurant_id,
        week_start_date=week_start_date,
    )
    if existing_prediction is not None:
        return existing_prediction

    # 2) Si no existe, generar con el modelo ML
    season_tag = infer_season_from_date(week_start_date)

    try:
        from app.ml.ml_model.predict_weekly_menu import generate_weekly_predictions_ml
    except Exception as exc:
        raise RuntimeError(f"Failed to import ML prediction module: {exc}") from exc

    training_df = await get_menu_items_training_df_for_restaurant(restaurant_id)

    try:
        predicted_menu_items = generate_weekly_predictions_ml(
            training_df=training_df,
            restaurant_id=restaurant_id,
            season_tag=season_tag,
            top_firsts=3,
            top_seconds=3,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to generate ML weekly predictions: {exc}") from exc

    model_version = predicted_menu_items.get(
        "model_version",
        "rf_binary_candidate_ranker_v1",
    )

    # 3) Guardar y devolver
    prediction_data = await save_weekly_prediction(
        restaurant_id=restaurant_id,
        week_start_date=week_start_date,
        predicted_menu_items=predicted_menu_items,
        model_version=model_version,
    )

    return prediction_data