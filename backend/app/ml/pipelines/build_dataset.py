import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    raise ValueError("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en el .env")

supabase: Client = create_client(url, key)

response = supabase.table("menu_items_training").select("*").execute()
data = response.data or []

if not data:
    raise ValueError("La vista menu_items_training no devolvió datos")

df = pd.DataFrame(data)

# -----------------------------
# Limpieza y tipado
# -----------------------------
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

df["weekday"] = df["date"].dt.day_name().str.lower()

# Evitar perder filas por NaN en groupby
df["season_tag"] = df["season_tag"].fillna("unknown")
df["normalized_name"] = df["normalized_name"].fillna("unknown")
df["category"] = df["category"].fillna("unknown")

# Numéricos
df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce").fillna(0)
df["avg_rating"] = pd.to_numeric(df["avg_rating"], errors="coerce")
df["rating_count"] = pd.to_numeric(df["rating_count"], errors="coerce").fillna(0)

# Opcional: si quieres que platos sin ratings no rompan medias
# puedes dejarlos como NaN o imputarlos.
# Yo recomiendo dejar NaN en avg_rating aquí y rellenar después en dish_stats si hace falta.

# Filtrar solo categorías válidas
df = df[df["category"].isin(["primero", "segundo"])]

# Filtrar platos normalizados válidos
df = df[df["normalized_name"].str.strip() != ""]
df = df[df["normalized_name"] != "unknown"]

# -----------------------------
# Export del dataset base
# -----------------------------
df.to_csv("../data/raw/menu_items_training.csv", index=False)

print("Dataset base generado:")
print(df.head())
print(f"Filas en dataset base: {len(df)}")

# -----------------------------
# Construcción de dish_stats
# -----------------------------
dish_stats = (
    df.groupby(
        ["restaurant_id", "season_tag", "weekday", "category", "normalized_name"],
        dropna=False
    )
    .agg(
        avg_units_sold=("units_sold", "mean"),
        avg_rating=("avg_rating", "mean"),
        times_used=("menu_item_id", "count"),
        total_units_sold=("units_sold", "sum"),
        total_ratings=("rating_count", "sum"),
    )
    .reset_index()
)

# Redondear para dejarlo más legible
dish_stats["avg_units_sold"] = dish_stats["avg_units_sold"].round(2)
dish_stats["avg_rating"] = dish_stats["avg_rating"].round(2)

# Opcional: si quieres imputar platos sin rating con un valor neutro
# dish_stats["avg_rating"] = dish_stats["avg_rating"].fillna(0)

dish_stats.to_csv("../data/interim/dish_stats.csv", index=False)

print("\nDish stats generado:")
print(dish_stats.head())
print(f"Filas en dish_stats: {len(dish_stats)}")

print(df["category"].value_counts())
print(df["season_tag"].value_counts())
print(df["normalized_name"].nunique())