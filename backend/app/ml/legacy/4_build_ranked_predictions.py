import pandas as pd


INPUT_FILE = "data/dish_stats.csv"
OUTPUT_FILE = "data/ranked_predictions.csv"

WEIGHT_UNITS = 0.50
WEIGHT_RATING = 0.30
WEIGHT_USAGE = 0.20

TOP_N = 4


def minmax_score(series: pd.Series) -> pd.Series:
    min_val = series.min()
    max_val = series.max()

    if pd.isna(min_val) or pd.isna(max_val):
        return pd.Series([0.0] * len(series), index=series.index)

    if max_val == min_val:
        return pd.Series([1.0] * len(series), index=series.index)

    return (series - min_val) / (max_val - min_val)


def rank_group(group: pd.DataFrame) -> pd.DataFrame:
    group = group.copy()

    group["units_score"] = minmax_score(group["avg_units_sold"])
    group["rating_score"] = minmax_score(group["avg_rating"].fillna(0))
    group["usage_score"] = minmax_score(group["times_used"])

    group["raw_score"] = (
        WEIGHT_UNITS * group["units_score"]
        + WEIGHT_RATING * group["rating_score"]
        + WEIGHT_USAGE * group["usage_score"]
    )

    # penalización suave por poca evidencia histórica
    group["confidence_factor"] = (group["times_used"] / 3).clip(upper=1.0)

    group["score"] = group["raw_score"] * group["confidence_factor"]

    group = group.sort_values(
        by=["score", "avg_units_sold", "avg_rating", "times_used"],
        ascending=[False, False, False, False]
    ).copy()

    group["rank"] = range(1, len(group) + 1)

    return group.head(TOP_N)


def main():
    df = pd.read_csv(INPUT_FILE)

    if df.empty:
        raise ValueError("dish_stats.csv está vacío")

    required_columns = [
        "restaurant_id",
        "season_tag",
        "weekday",
        "category",
        "normalized_name",
        "avg_units_sold",
        "avg_rating",
        "times_used",
        "total_units_sold",
        "total_ratings",
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(
            f"Faltan columnas en dish_stats.csv: {missing}. "
            f"Columnas actuales: {df.columns.tolist()}"
        )

    df["season_tag"] = df["season_tag"].fillna("unknown")
    df["weekday"] = df["weekday"].fillna("unknown")
    df["category"] = df["category"].fillna("unknown")
    df["normalized_name"] = df["normalized_name"].fillna("unknown")

    df["avg_units_sold"] = pd.to_numeric(df["avg_units_sold"], errors="coerce").fillna(0)
    df["avg_rating"] = pd.to_numeric(df["avg_rating"], errors="coerce").fillna(0)
    df["times_used"] = pd.to_numeric(df["times_used"], errors="coerce").fillna(0)
    df["total_units_sold"] = pd.to_numeric(df["total_units_sold"], errors="coerce").fillna(0)
    df["total_ratings"] = pd.to_numeric(df["total_ratings"], errors="coerce").fillna(0)

    grouped = df.groupby(
        ["restaurant_id", "season_tag", "weekday", "category"],
        dropna=False,
        sort=True
    )

    ranked_parts = []

    for (restaurant_id, season_tag, weekday, category), group in grouped:
        ranked_group = rank_group(group)

        # reinyectamos las claves del grupo
        ranked_group["restaurant_id"] = restaurant_id
        ranked_group["season_tag"] = season_tag
        ranked_group["weekday"] = weekday
        ranked_group["category"] = category

        ranked_parts.append(ranked_group)

    if not ranked_parts:
        raise ValueError("No se generaron rankings. Revisa dish_stats.csv")

    ranked = pd.concat(ranked_parts, ignore_index=True)

    ranked = ranked[
        [
            "restaurant_id",
            "season_tag",
            "weekday",
            "category",
            "normalized_name",
            "avg_units_sold",
            "avg_rating",
            "times_used",
            "total_units_sold",
            "total_ratings",
            "units_score",
            "rating_score",
            "usage_score",
            "raw_score",
            "confidence_factor",
            "score",
            "rank",
        ]
    ]

    ranked = ranked.sort_values(
        by=["restaurant_id", "season_tag", "weekday", "category", "rank"]
    ).reset_index(drop=True)

    ranked.to_csv(OUTPUT_FILE, index=False)

    print("Ranking generado correctamente")
    print(ranked.head(20))
    print(f"Total filas ranking: {len(ranked)}")


if __name__ == "__main__":
    main()