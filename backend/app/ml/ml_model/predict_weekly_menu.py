from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

import pandas as pd

from app.ml.ml_model.feature_builder import (
    build_candidate_features,
    build_candidate_pool,
    normalize_training_df,
)
from app.ml.ml_model.model_io import load_menu_model


FEATURE_COLUMNS = [
    "restaurant_id",
    "season_tag",
    "weekday",
    "category",
    "normalized_name",
    "avg_units_sold_hist",
    "avg_rating_hist",
    "times_used_hist",
    "total_units_sold_hist",
    "total_ratings_hist",
    "days_since_last_used",
    "used_prev_day",
    "used_7_days_ago",
    "used_14_days_ago",
    "times_used_same_weekday",
    "times_used_same_season",
    "usage_rate_global",
    "usage_rate_same_weekday",
    "usage_rate_same_season",
	"used_same_weekday_last_week",
	"used_same_weekday_last_2_weeks",
	"used_same_weekday_last_3_weeks",
]


WEEKDAYS_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday"]


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def infer_season_tag(history_df: pd.DataFrame, target_date: pd.Timestamp) -> str:
    valid = history_df[history_df["date"] <= target_date].sort_values("date")
    if valid.empty:
        return "unknown"
    return str(valid.iloc[-1]["season_tag"])


def next_week_monday(from_date: date | None = None) -> date:
    if from_date is None:
        from_date = date.today()

    days_ahead = (7 - from_date.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7

    return from_date + timedelta(days=days_ahead)


def build_next_week_dates() -> list[pd.Timestamp]:
    monday = next_week_monday()
    return [pd.Timestamp(monday + timedelta(days=i)) for i in range(5)]


# ---------------------------------------------------------
# Core ML scoring
# ---------------------------------------------------------


def build_candidate_score_table(
    training_df: pd.DataFrame,
    restaurant_id: str,
    target_date: pd.Timestamp,
    category: str,
    season_tag: str | None = None,
    max_history_days: int | None = None,
) -> pd.DataFrame:
    df = normalize_training_df(training_df)
    model = load_menu_model()

    restaurant_df = df[df["restaurant_id"] == restaurant_id].copy()
    if restaurant_df.empty:
        raise ValueError(f"No hay datos para restaurant_id={restaurant_id}")

    if season_tag is None:
        season_tag = infer_season_tag(restaurant_df, target_date)

    historical_df = restaurant_df[
        (restaurant_df["category"] == category)
        & (restaurant_df["date"] < target_date)
    ].copy()

    season_candidates = (
        historical_df[historical_df["season_tag"] == season_tag]["normalized_name"]
        .drop_duplicates()
        .tolist()
    )

    all_candidates = (
        historical_df["normalized_name"]
        .drop_duplicates()
        .tolist()
    )

    # Si hay suficientes candidatos de temporada, usar solo esos
    min_candidates_required = 6  # ajústalo si quieres
    if len(season_candidates) >= min_candidates_required:
        candidates = season_candidates
    else:
        candidates = all_candidates

    rows = []

    for dish in candidates:
        features = build_candidate_features(
            history_df=restaurant_df,
            restaurant_id=restaurant_id,
            target_date=target_date,
            season_tag=season_tag,
            category=category,
            dish_name=dish,
            max_history_days=max_history_days,
        )
        rows.append(features)

    if not rows:
        return pd.DataFrame()

    score_df = pd.DataFrame(rows)

    score_df = score_df[score_df["times_used_hist"] > 0].copy()
    if score_df.empty:
        return pd.DataFrame()

    score_df["score"] = model.predict_proba(score_df[FEATURE_COLUMNS])[:, 1]

    score_df["seasonal_penalty"] = 0.0

    # Penaliza platos nunca usados en esa temporada
    score_df.loc[score_df["times_used_same_season"] == 0, "seasonal_penalty"] = 0.20

    # Penaliza también platos con uso de temporada muy bajo
    score_df.loc[
        (score_df["times_used_same_season"] > 0) & (score_df["usage_rate_same_season"] < 0.05),
        "seasonal_penalty"
    ] = 0.10

    score_df["final_score"] = score_df["score"] - score_df["seasonal_penalty"]

    score_df = score_df.sort_values(
        by=["final_score", "times_used_same_season", "times_used_hist", "avg_units_sold_hist"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)

    score_df["rank"] = range(1, len(score_df) + 1)
    return score_df


# ---------------------------------------------------------
# Selection logic (reuse baseline ideas)
# ---------------------------------------------------------


def pick_diverse_items(
    candidates: pd.DataFrame,
    used_counts: dict,
    previous_day_items: set[str],
    top_n: int,
    max_repeats_per_week: int = 2,
) -> list[dict]:
    selected = []

    for _, row in candidates.iterrows():
        dish = row["normalized_name"]

        if used_counts.get(dish, 0) >= max_repeats_per_week:
            continue

        if dish in previous_day_items:
            continue

        selected.append(
            {
                "normalized_name": dish,
                "score": float(row["score"]),
                "rank": int(row["rank"]),
                "avg_units_sold_hist": float(row["avg_units_sold_hist"]),
                "avg_rating_hist": float(row["avg_rating_hist"]),
                "times_used_hist": int(row["times_used_hist"]),
            }
        )

        used_counts[dish] = used_counts.get(dish, 0) + 1

        if len(selected) >= top_n:
            break

    return selected


# ---------------------------------------------------------
# MAIN FUNCTION (THIS IS WHAT YOU NEED)
# ---------------------------------------------------------


def generate_weekly_predictions_ml(
    training_df: pd.DataFrame,
    restaurant_id: str,
    season_tag: str | None = None,
    top_firsts: int = 4,
    top_seconds: int = 4,
) -> dict:
    df = normalize_training_df(training_df)

    week_dates = build_next_week_dates()

    result = {
        "restaurant_id": restaurant_id,
        "season_tag": season_tag or "auto",
        "model_version": "rf_binary_candidate_ranker_v1",
        "days": [],
    }

    weekly_used_firsts = defaultdict(int)
    weekly_used_seconds = defaultdict(int)

    prev_firsts = set()
    prev_seconds = set()

    for target_date in week_dates:
        restaurant_df = df[df["restaurant_id"] == restaurant_id]

        inferred_season = season_tag or infer_season_tag(
            restaurant_df,
            target_date,
        )

        firsts_candidates = build_candidate_score_table(
            training_df=df,
            restaurant_id=restaurant_id,
            target_date=target_date,
            category="primero",
            season_tag=inferred_season,
        )

        seconds_candidates = build_candidate_score_table(
            training_df=df,
            restaurant_id=restaurant_id,
            target_date=target_date,
            category="segundo",
            season_tag=inferred_season,
        )

        primeros = pick_diverse_items(
            candidates=firsts_candidates,
            used_counts=weekly_used_firsts,
            previous_day_items=prev_firsts,
            top_n=top_firsts,
        )

        segundos = pick_diverse_items(
            candidates=seconds_candidates,
            used_counts=weekly_used_seconds,
            previous_day_items=prev_seconds,
            top_n=top_seconds,
        )

        result["days"].append(
            {
                "date": target_date.strftime("%Y-%m-%d"),
                "weekday": target_date.day_name().lower(),
                "season_tag": inferred_season,
                "primeros": primeros,
                "segundos": segundos,
            }
        )

        prev_firsts = {x["normalized_name"] for x in primeros}
        prev_seconds = {x["normalized_name"] for x in segundos}

    return result
