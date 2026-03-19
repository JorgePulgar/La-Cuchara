from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


VALID_CATEGORIES = {"primero", "segundo"}
DEFAULT_UNKNOWN_SEASON = "unknown"


@dataclass
class FeatureBuilderConfig:
    max_history_days: int | None = 120


def normalize_training_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y tipa el dataframe base procedente de menu_items_training.
    Espera columnas:
        - menu_item_id
        - restaurant_id
        - date
        - season_tag
        - normalized_name
        - category
        - avg_rating
        - rating_count
        - units_sold
    """
    out = df.copy()

    required_columns = [
        "menu_item_id",
        "restaurant_id",
        "date",
        "season_tag",
        "normalized_name",
        "category",
        "avg_rating",
        "rating_count",
        "units_sold",
    ]
    missing = [col for col in required_columns if col not in out.columns]
    if missing:
        raise ValueError(
            f"Faltan columnas en el dataset de entrenamiento: {missing}. "
            f"Columnas actuales: {out.columns.tolist()}"
        )

    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).copy()

    out["season_tag"] = out["season_tag"].fillna(DEFAULT_UNKNOWN_SEASON).astype(str)
    out["normalized_name"] = (
        out["normalized_name"].fillna("").astype(str).str.strip().str.lower()
    )
    out["category"] = out["category"].fillna("").astype(str).str.strip().str.lower()

    out = out[out["category"].isin(VALID_CATEGORIES)].copy()
    out = out[out["normalized_name"] != ""].copy()
    out = out[out["normalized_name"] != "unknown"].copy()

    out["avg_rating"] = pd.to_numeric(out["avg_rating"], errors="coerce")
    out["rating_count"] = pd.to_numeric(out["rating_count"], errors="coerce").fillna(0)
    out["units_sold"] = pd.to_numeric(out["units_sold"], errors="coerce").fillna(0)

    out["weekday"] = out["date"].dt.day_name().str.lower()

    return out.sort_values(
        ["restaurant_id", "date", "category", "normalized_name"]
    ).reset_index(drop=True)


def build_candidate_pool(df: pd.DataFrame) -> pd.DataFrame:
    """
    Catálogo histórico de platos por restaurante y categoría.
    """
    return (
        df[["restaurant_id", "category", "normalized_name"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )


def _safe_mean(series: pd.Series, default: float = 0.0) -> float:
    if len(series) == 0:
        return default
    value = series.mean()
    return default if pd.isna(value) else float(value)


def _safe_sum(series: pd.Series) -> float:
    if len(series) == 0:
        return 0.0
    return float(series.fillna(0).sum())


def _clip_history_window(
    hist: pd.DataFrame,
    target_date: pd.Timestamp,
    max_history_days: int | None,
) -> pd.DataFrame:
    if max_history_days is None:
        return hist

    start_date = target_date - pd.Timedelta(days=max_history_days)
    return hist[hist["date"] >= start_date].copy()


def build_candidate_features(
    history_df: pd.DataFrame,
    restaurant_id: str,
    target_date: pd.Timestamp,
    season_tag: str,
    category: str,
    dish_name: str,
    max_history_days: int | None = 120,
) -> dict:
    """
    Construye las features para un plato candidato en una fecha concreta.
    SOLO usa histórico anterior a target_date para evitar leakage.
    """
    hist = history_df[
        (history_df["restaurant_id"] == restaurant_id)
        & (history_df["category"] == category)
        & (history_df["date"] < target_date)
    ].copy()

    hist = _clip_history_window(hist, target_date, max_history_days)
    dish_hist = hist[hist["normalized_name"] == dish_name].sort_values("date").copy()

    weekday = target_date.day_name().lower()

    times_used_hist = int(len(dish_hist))
    total_units_sold_hist = _safe_sum(dish_hist["units_sold"])
    avg_units_sold_hist = _safe_mean(dish_hist["units_sold"], 0.0)
    avg_rating_hist = _safe_mean(dish_hist["avg_rating"].dropna(), 0.0)
    total_ratings_hist = _safe_sum(dish_hist["rating_count"])

    if not dish_hist.empty:
        last_used_date = dish_hist["date"].max()
        days_since_last_used = int((target_date - last_used_date).days)
    else:
        days_since_last_used = 9999

    dish_dates = set(dish_hist["date"].tolist())

    used_prev_day = int((target_date - pd.Timedelta(days=1)) in dish_dates)
    used_7_days_ago = int((target_date - pd.Timedelta(days=7)) in dish_dates)
    used_14_days_ago = int((target_date - pd.Timedelta(days=14)) in dish_dates)

    hist_same_weekday = dish_hist[dish_hist["date"].dt.day_name().str.lower() == weekday]
    times_used_same_weekday = int(len(hist_same_weekday))

    hist_same_season = dish_hist[dish_hist["season_tag"] == season_tag]
    times_used_same_season = int(len(hist_same_season))

    total_hist_rows = max(1, len(hist))
    usage_rate_global = times_used_hist / total_hist_rows
    usage_rate_same_weekday = times_used_same_weekday / total_hist_rows
    usage_rate_same_season = times_used_same_season / total_hist_rows

    used_same_weekday_last_week = int(
        (target_date - pd.Timedelta(days=7)) in dish_dates
    )
    used_same_weekday_last_2_weeks = int(
        (target_date - pd.Timedelta(days=14)) in dish_dates
    )
    used_same_weekday_last_3_weeks = int(
        (target_date - pd.Timedelta(days=21)) in dish_dates
    )

    return {
        "restaurant_id": restaurant_id,
        "menu_date": pd.Timestamp(target_date),
        "season_tag": season_tag or DEFAULT_UNKNOWN_SEASON,
        "weekday": weekday,
        "category": category,
        "normalized_name": dish_name,
        "avg_units_sold_hist": avg_units_sold_hist,
        "avg_rating_hist": avg_rating_hist,
        "times_used_hist": times_used_hist,
        "total_units_sold_hist": total_units_sold_hist,
        "total_ratings_hist": total_ratings_hist,
        "days_since_last_used": days_since_last_used,
        "used_prev_day": used_prev_day,
        "used_7_days_ago": used_7_days_ago,
        "used_14_days_ago": used_14_days_ago,
        "times_used_same_weekday": times_used_same_weekday,
        "times_used_same_season": times_used_same_season,
        "usage_rate_global": usage_rate_global,
        "usage_rate_same_weekday": usage_rate_same_weekday,
        "usage_rate_same_season": usage_rate_same_season,
        "used_same_weekday_last_week": used_same_weekday_last_week,
        "used_same_weekday_last_2_weeks": used_same_weekday_last_2_weeks,
        "used_same_weekday_last_3_weeks": used_same_weekday_last_3_weeks,
    }


def build_supervised_dataset(
    training_df: pd.DataFrame,
    max_history_days: int | None = 120,
) -> pd.DataFrame:
    """
    Construye dataset supervisado binario por candidato.

    Cada fila representa:
        (restaurant_id, menu_date, category, normalized_name) -> target_selected

    target_selected = 1 si el plato apareció en ese día/categoría
    target_selected = 0 si no apareció
    """
    df = normalize_training_df(training_df)
    candidate_pool = build_candidate_pool(df)

    contexts = (
        df[["restaurant_id", "date", "season_tag", "weekday", "category"]]
        .drop_duplicates()
        .sort_values(["restaurant_id", "date", "category"])
        .reset_index(drop=True)
    )

    rows: list[dict] = []

    for _, ctx in contexts.iterrows():
        restaurant_id = ctx["restaurant_id"]
        menu_date = pd.Timestamp(ctx["date"])
        season_tag = ctx["season_tag"]
        category = ctx["category"]

        served_today = set(
            df[
                (df["restaurant_id"] == restaurant_id)
                & (df["date"] == menu_date)
                & (df["category"] == category)
            ]["normalized_name"].tolist()
        )

        candidates = candidate_pool[
            (candidate_pool["restaurant_id"] == restaurant_id)
            & (candidate_pool["category"] == category)
        ]["normalized_name"].tolist()

        for dish_name in candidates:
            feat_row = build_candidate_features(
                history_df=df,
                restaurant_id=restaurant_id,
                target_date=menu_date,
                season_tag=season_tag,
                category=category,
                dish_name=dish_name,
                max_history_days=max_history_days,
            )
            feat_row["target_selected"] = int(dish_name in served_today)
            rows.append(feat_row)

    if not rows:
        raise ValueError("No se pudo construir el dataset supervisado: no hay filas")

    supervised_df = pd.DataFrame(rows).sort_values(
        ["restaurant_id", "menu_date", "category", "normalized_name"]
    )

    # 1) Filtrar filas sin histórico útil
    supervised_df = supervised_df[
        supervised_df["times_used_hist"] > 0
    ].copy()

    if supervised_df.empty:
        raise ValueError("Dataset vacío tras filtrar históricos")

    # 2) Balancear clases: mantener todos los positivos y muestrear negativos
    positives = supervised_df[supervised_df["target_selected"] == 1].copy()
    negatives = supervised_df[supervised_df["target_selected"] == 0].copy()

    if positives.empty:
        raise ValueError("No hay ejemplos positivos tras el filtrado")

    # ratio 1:3 -> por cada positivo, como mucho 3 negativos
    max_negatives = len(positives) * 3

    if len(negatives) > max_negatives:
        negatives = negatives.sample(
            n=max_negatives,
            random_state=42,
        )

    supervised_df = pd.concat([positives, negatives], ignore_index=True)
    supervised_df = supervised_df.sample(frac=1, random_state=42).reset_index(drop=True)

    return supervised_df
