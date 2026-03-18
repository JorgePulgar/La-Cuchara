import pandas as pd

WEEKDAYS_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday"]
TOP_FIRSTS = 4
TOP_SECONDS = 4


def load_ranked_predictions(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    if df.empty:
        raise ValueError("ranked_predictions.csv está vacío")

    required_columns = [
        "restaurant_id",
        "season_tag",
        "weekday",
        "category",
        "normalized_name",
        "score",
        "rank",
        "avg_units_sold",
        "avg_rating",
        "times_used",
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(
            f"Faltan columnas en ranked_predictions.csv: {missing}. "
            f"Columnas actuales: {df.columns.tolist()}"
        )

    df["restaurant_id"] = df["restaurant_id"].astype(str)
    df["season_tag"] = df["season_tag"].fillna("unknown").astype(str)
    df["weekday"] = df["weekday"].fillna("unknown").astype(str)
    df["category"] = df["category"].fillna("unknown").astype(str)
    df["normalized_name"] = df["normalized_name"].fillna("unknown").astype(str)
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce").fillna(9999)
    df["avg_units_sold"] = pd.to_numeric(df["avg_units_sold"], errors="coerce").fillna(0)
    df["avg_rating"] = pd.to_numeric(df["avg_rating"], errors="coerce").fillna(0)
    df["times_used"] = pd.to_numeric(df["times_used"], errors="coerce").fillna(0)

    return df


def pick_diverse_items(
    candidates: pd.DataFrame,
    used_counts: dict,
    previous_day_items: set,
    top_n: int = 4,
    max_weekly_repeats: int = 2,
) -> list[dict]:
    selected = []

    for _, row in candidates.iterrows():
        dish = row["normalized_name"]

        if used_counts.get(dish, 0) >= max_weekly_repeats:
            continue

        if dish in previous_day_items:
            continue

        selected.append(
            {
                "normalized_name": row["normalized_name"],
                "score": float(row["score"]),
                "rank": int(row["rank"]),
                "avg_units_sold": float(row["avg_units_sold"]),
                "avg_rating": float(row["avg_rating"]),
                "times_used": int(row["times_used"]),
            }
        )

        used_counts[dish] = used_counts.get(dish, 0) + 1

        if len(selected) == top_n:
            break

    return selected


def generate_week_menu(
    df: pd.DataFrame,
    restaurant_id: str,
    season_tag: str,
    weekdays: list[str] | None = None,
) -> dict:
    if weekdays is None:
        weekdays = WEEKDAYS_ORDER

    result = {
        "restaurant_id": restaurant_id,
        "season_tag": season_tag,
        "days": [],
    }

    weekly_used_firsts = {}
    weekly_used_seconds = {}

    prev_firsts = set()
    prev_seconds = set()

    for weekday in weekdays:
        day_df = df[
            (df["restaurant_id"] == restaurant_id)
            & (df["season_tag"] == season_tag)
            & (df["weekday"] == weekday)
        ].copy()

        firsts_candidates = day_df[day_df["category"] == "primero"].sort_values(
            by=["rank", "score"], ascending=[True, False]
        )

        seconds_candidates = day_df[day_df["category"] == "segundo"].sort_values(
            by=["rank", "score"], ascending=[True, False]
        )

        primeros = pick_diverse_items(
            candidates=firsts_candidates,
            used_counts=weekly_used_firsts,
            previous_day_items=prev_firsts,
            top_n=TOP_FIRSTS,
            max_weekly_repeats=2,
        )

        segundos = pick_diverse_items(
            candidates=seconds_candidates,
            used_counts=weekly_used_seconds,
            previous_day_items=prev_seconds,
            top_n=TOP_SECONDS,
            max_weekly_repeats=2,
        )

        result["days"].append(
            {
                "weekday": weekday,
                "primeros": primeros,
                "segundos": segundos,
            }
        )

        prev_firsts = {item["normalized_name"] for item in primeros}
        prev_seconds = {item["normalized_name"] for item in segundos}

    return result


def generate_weekly_predictions(
    restaurant_id: str,
    season_tag: str,
    input_file: str = "data/ranked_predictions.csv",
) -> dict:
    df = load_ranked_predictions(input_file)
    return generate_week_menu(
        df=df,
        restaurant_id=restaurant_id,
        season_tag=season_tag,
    )