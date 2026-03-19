import json
import pandas as pd


INPUT_FILE = "data/ranked_predictions.csv"
OUTPUT_FILE = "data/weekly_predictions.json"

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
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(
            f"Faltan columnas en ranked_predictions.csv: {missing}. "
            f"Columnas actuales: {df.columns.tolist()}"
        )

    df["season_tag"] = df["season_tag"].fillna("unknown")
    df["weekday"] = df["weekday"].fillna("unknown")
    df["category"] = df["category"].fillna("unknown")
    df["normalized_name"] = df["normalized_name"].fillna("unknown")
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce").fillna(9999)

    return df


def get_day_predictions(
    df: pd.DataFrame,
    restaurant_id: str,
    season_tag: str,
    weekday: str,
    top_firsts: int = TOP_FIRSTS,
    top_seconds: int = TOP_SECONDS,
) -> dict:
    day_df = df[
        (df["restaurant_id"] == restaurant_id)
        & (df["season_tag"] == season_tag)
        & (df["weekday"] == weekday)
    ].copy()

    firsts = (
        day_df[day_df["category"] == "primero"]
        .sort_values(by=["rank", "score"], ascending=[True, False])
        .head(top_firsts)
    )

    seconds = (
        day_df[day_df["category"] == "segundo"]
        .sort_values(by=["rank", "score"], ascending=[True, False])
        .head(top_seconds)
    )

    return {
        "weekday": weekday,
        "primeros": firsts[
            [
                "normalized_name",
                "score",
                "rank",
                "avg_units_sold",
                "avg_rating",
                "times_used",
            ]
        ].to_dict(orient="records"),
        "segundos": seconds[
            [
                "normalized_name",
                "score",
                "rank",
                "avg_units_sold",
                "avg_rating",
                "times_used",
            ]
        ].to_dict(orient="records"),
    }


def generate_week_menu(df, restaurant_id, season_tag, weekdays=None):
    if weekdays is None:
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    result = {"restaurant_id": restaurant_id, "season_tag": season_tag, "days": []}

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
            top_n=4,
            max_weekly_repeats=2,
        )

        segundos = pick_diverse_items(
            candidates=seconds_candidates,
            used_counts=weekly_used_seconds,
            previous_day_items=prev_seconds,
            top_n=4,
            max_weekly_repeats=2,
        )

        result["days"].append(
            {"weekday": weekday, "primeros": primeros, "segundos": segundos}
        )

        prev_firsts = {item["normalized_name"] for item in primeros}
        prev_seconds = {item["normalized_name"] for item in segundos}

    return result


def print_week_menu(week_menu: dict) -> None:
    print("\n==============================")
    print(f"RESTAURANT: {week_menu['restaurant_id']}")
    print(f"SEASON: {week_menu['season_tag']}")
    print("==============================")

    for day in week_menu["days"]:
        print(f"\n{day['weekday'].upper()}")

        print("  Primeros:")
        if day["primeros"]:
            for item in day["primeros"]:
                print(
                    f"    {item['rank']}. {item['normalized_name']} "
                    f"(score={item['score']:.3f}, sold={item['avg_units_sold']}, "
                    f"rating={item['avg_rating']}, used={item['times_used']})"
                )
        else:
            print("    Sin propuestas")

        print("  Segundos:")
        if day["segundos"]:
            for item in day["segundos"]:
                print(
                    f"    {item['rank']}. {item['normalized_name']} "
                    f"(score={item['score']:.3f}, sold={item['avg_units_sold']}, "
                    f"rating={item['avg_rating']}, used={item['times_used']})"
                )
        else:
            print("    Sin propuestas")


def pick_diverse_items(
    candidates, used_counts, previous_day_items, top_n=4, max_weekly_repeats=2
):
    selected = []

    for _, row in candidates.iterrows():
        dish = row["normalized_name"]

        # evitar repetir demasiadas veces en la semana
        if used_counts.get(dish, 0) >= max_weekly_repeats:
            continue

        # penalizar si salió el día anterior
        if dish in previous_day_items:
            continue

        selected.append(
            {
                "normalized_name": row["normalized_name"],
                "score": row["score"],
                "rank": row["rank"],
                "avg_units_sold": row["avg_units_sold"],
                "avg_rating": row["avg_rating"],
                "times_used": row["times_used"],
            }
        )

        used_counts[dish] = used_counts.get(dish, 0) + 1

        if len(selected) == top_n:
            break

    return selected


def main():
    df = load_ranked_predictions(INPUT_FILE)

    # Cambia estos valores para probar
    restaurant_id = "020d9e35-a7eb-4a3d-a275-437e8227aa8b"
    season_tag = "otono"

    week_menu = generate_week_menu(
        df=df,
        restaurant_id=restaurant_id,
        season_tag=season_tag,
    )

    print_week_menu(week_menu)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(week_menu, f, ensure_ascii=False, indent=2)

    print(f"\nJSON guardado en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
