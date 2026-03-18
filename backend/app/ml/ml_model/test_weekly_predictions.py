from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.ml.ml_model.predict_weekly_menu import generate_weekly_predictions_ml


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "raw" / "menu_items_training.csv"
OUTPUT_FILE = BASE_DIR / "data" / "weekly_predictions_ml.json"


def print_week_menu(week_menu: dict) -> None:
    print("\n==============================")
    print(f"RESTAURANT: {week_menu['restaurant_id']}")
    print(f"MODEL: {week_menu['model_version']}")
    print(f"SEASON: {week_menu['season_tag']}")
    print("==============================")

    for day in week_menu["days"]:
        print(f"\n{day['weekday'].upper()} ({day['date']})")

        print("  Primeros:")
        if day["primeros"]:
            for item in day["primeros"]:
                print(
                    f"    {item['rank']}. {item['normalized_name']} "
                    f"(score={item['score']:.3f}, "
                    f"sold={item['avg_units_sold_hist']:.2f}, "
                    f"rating={item['avg_rating_hist']:.2f}, "
                    f"used={item['times_used_hist']})"
                )
        else:
            print("    Sin propuestas")

        print("  Segundos:")
        if day["segundos"]:
            for item in day["segundos"]:
                print(
                    f"    {item['rank']}. {item['normalized_name']} "
                    f"(score={item['score']:.3f}, "
                    f"sold={item['avg_units_sold_hist']:.2f}, "
                    f"rating={item['avg_rating_hist']:.2f}, "
                    f"used={item['times_used_hist']})"
                )
        else:
            print("    Sin propuestas")


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"No existe el archivo base: {INPUT_FILE}. "
            "Genera antes menu_items_training.csv"
        )

    df = pd.read_csv(INPUT_FILE)

    # Cambia estos valores para probar
    restaurant_id = "020d9e35-a7eb-4a3d-a275-437e8227aa8b"
    season_tag = "primavera"  # o None para inferirla automáticamente

    week_menu = generate_weekly_predictions_ml(
        training_df=df,
        restaurant_id=restaurant_id,
        season_tag=season_tag,
        top_firsts=3,
        top_seconds=3,
    )

    print_week_menu(week_menu)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(week_menu, f, ensure_ascii=False, indent=2)

    print(f"\nJSON guardado en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()