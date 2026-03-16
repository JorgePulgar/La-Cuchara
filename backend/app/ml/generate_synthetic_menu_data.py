#!/usr/bin/env python3
"""
generate_synthetic_data.py

Genera datos sintéticos de menús para restaurantes en Supabase.
Diseñado para que los nombres de platos sean fáciles de normalizar después.

Genera:
- menus
- menu_items
- menu_item_sales

Opcional:
- ratings (desactivado por defecto)

Requisitos:
    pip install supabase python-dotenv

Variables de entorno:
    SUPABASE_URL=...
    SUPABASE_SERVICE_ROLE_KEY=...

Uso:
    python generate_synthetic_data.py
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client


# =========================================================
# CONFIG
# =========================================================

START_DATE = date(2025, 11, 1)
END_DATE = date(2026, 2, 28)

FIRSTS_PER_DAY = (3, 4)   # rango aleatorio
SECONDS_PER_DAY = (3, 4)

CREATE_RATINGS = True
RATINGS_PER_ITEM_RANGE = (0, 6)

DRY_RUN = False


# =========================================================
# HELPERS
# =========================================================

def daterange(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def is_weekday(d: date) -> bool:
    return d.weekday() < 5  # lunes-viernes


def get_season(d: date) -> str:
    m = d.month
    if m in (12, 1, 2):
        return "invierno"
    if m in (3, 4, 5):
        return "primavera"
    if m in (6, 7, 8):
        return "verano"
    return "otono"


def weekday_name_es(d: date) -> str:
    names = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    return names[d.weekday()]


def chunked(seq: list[dict[str, Any]], size: int):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


# =========================================================
# MODELO DE PLATOS
# =========================================================

@dataclass
class Dish:
    canonical: str
    category: str   # primero | segundo
    variants: list[str]
    popularity: int  # base para ventas
    rating_base: float


FIRST_DISHES = [
    Dish("lentejas", "primero",
         ["Lentejas", "Lentejas caseras", "Lentejas estofadas"], 48, 4.4),
    Dish("fabada", "primero",
         ["Fabada", "Fabada asturiana"], 40, 4.3),
    Dish("cocido", "primero",
         ["Cocido", "Cocido madrileño", "Cocido madrileno"], 50, 4.5),
    Dish("garbanzos", "primero",
         ["Garbanzos", "Garbanzos guisados"], 34, 4.0),
    Dish("judias_verdes", "primero",
         ["Judías verdes", "Judias verdes con jamón", "Judias verdes"], 26, 3.8),
    Dish("sopa_castellana", "primero",
         ["Sopa castellana"], 30, 4.1),
    Dish("sopa_verduras", "primero",
         ["Sopa de verduras"], 24, 3.9),
    Dish("crema_verduras", "primero",
         ["Crema de verduras"], 22, 3.9),
    Dish("crema_calabaza", "primero",
         ["Crema de calabaza"], 25, 4.0),
    Dish("crema_calabacin", "primero",
         ["Crema de calabacín", "Crema de calabacin"], 23, 3.9),
    Dish("ensalada_mixta", "primero",
         ["Ensalada mixta"], 28, 3.8),
    Dish("ensalada_cesar", "primero",
         ["Ensalada César", "Ensalada Cesar"], 26, 3.9),
    Dish("ensalada_pasta", "primero",
         ["Ensalada de pasta"], 22, 3.8),
    Dish("ensalada_campera", "primero",
         ["Ensalada campera"], 29, 4.0),
    Dish("ensalada_arroz", "primero",
         ["Ensalada de arroz"], 21, 3.8),
    Dish("arroz_cubana", "primero",
         ["Arroz a la cubana"], 33, 4.1),
    Dish("arroz_tres_delicias", "primero",
         ["Arroz tres delicias"], 27, 3.9),
    Dish("paella", "primero",
         ["Paella", "Paella mixta"], 44, 4.3),
    Dish("arroz_pollo", "primero",
         ["Arroz con pollo"], 36, 4.1),
    Dish("macarrones", "primero",
         ["Macarrones"], 31, 4.0),
    Dish("macarrones_tomate", "primero",
         ["Macarrones con tomate"], 28, 3.9),
    Dish("macarrones_bolonesa", "primero",
         ["Macarrones a la boloñesa", "Macarrones boloñesa", "Macarrones a la bolonesa"], 42, 4.3),
    Dish("espaguetis_carbonara", "primero",
         ["Espaguetis carbonara", "Espaguetis a la carbonara"], 35, 4.1),
    Dish("espaguetis_bolonesa", "primero",
         ["Espaguetis boloñesa", "Espaguetis a la boloñesa"], 33, 4.0),
    Dish("pure_verduras", "primero",
         ["Puré de verduras", "Pure de verduras"], 19, 3.8),
    Dish("gazpacho", "primero",
         ["Gazpacho"], 30, 4.0),
    Dish("salmorejo", "primero",
         ["Salmorejo"], 29, 4.1),
]

SECOND_DISHES = [
    Dish("merluza_plancha", "segundo",
         ["Merluza a la plancha", "Filete de merluza a la plancha"], 40, 4.2),
    Dish("merluza_rebozada", "segundo",
         ["Merluza rebozada"], 31, 4.0),
    Dish("bacalao", "segundo",
         ["Bacalao"], 28, 4.1),
    Dish("bacalao_plancha", "segundo",
         ["Bacalao a la plancha"], 27, 4.0),
    Dish("pollo_asado", "segundo",
         ["Pollo asado", "Pollo al horno"], 46, 4.3),
    Dish("pollo_empanado", "segundo",
         ["Pollo empanado", "Filete de pollo empanado"], 38, 4.1),
    Dish("pollo_plancha", "segundo",
         ["Pollo a la plancha", "Pechuga de pollo a la plancha"], 33, 4.0),
    Dish("filete_ternera", "segundo",
         ["Filete de ternera"], 37, 4.2),
    Dish("ternera_plancha", "segundo",
         ["Ternera a la plancha"], 29, 4.0),
    Dish("escalope_ternera", "segundo",
         ["Escalope de ternera"], 35, 4.1),
    Dish("filete_empanado", "segundo",
         ["Filete empanado"], 32, 4.0),
    Dish("secreto_iberico", "segundo",
         ["Secreto ibérico", "Secreto iberico"], 34, 4.3),
    Dish("costillas_horno", "segundo",
         ["Costillas al horno"], 36, 4.2),
    Dish("chuletas_cerdo", "segundo",
         ["Chuletas de cerdo"], 30, 3.9),
    Dish("lomo_plancha", "segundo",
         ["Lomo a la plancha"], 27, 3.8),
    Dish("lomo_empanado", "segundo",
         ["Lomo empanado"], 31, 3.9),
    Dish("albondigas", "segundo",
         ["Albóndigas", "Albóndigas en salsa", "Albondigas en salsa"], 39, 4.2),
    Dish("hamburguesa", "segundo",
         ["Hamburguesa", "Hamburguesa completa"], 28, 3.9),
    Dish("tortilla_patata", "segundo",
         ["Tortilla de patata"], 26, 4.0),
    Dish("revuelto_setas", "segundo",
         ["Revuelto de setas"], 22, 3.9),
    Dish("calamares_romana", "segundo",
         ["Calamares a la romana"], 29, 4.0),
    Dish("boquerones_fritos", "segundo",
         ["Boquerones fritos"], 25, 3.9),
    Dish("pescado_dia", "segundo",
         ["Pescado del día", "Pescado del dia"], 24, 3.9),
    Dish("carne_dia", "segundo",
         ["Carne del día", "Carne del dia"], 24, 3.9),
]


# =========================================================
# PLANTILLAS POR TEMPORADA
# =========================================================

SEASON_POOL = {
    "invierno": {
        "primero": [
            "lentejas", "fabada", "cocido", "garbanzos", "sopa_castellana",
            "sopa_verduras", "crema_verduras", "crema_calabaza", "crema_calabacin",
            "judias_verdes", "macarrones_bolonesa", "paella"
        ],
        "segundo": [
            "pollo_asado", "pollo_empanado", "merluza_plancha", "albondigas",
            "filete_ternera", "costillas_horno", "bacalao", "lomo_empanado",
            "secreto_iberico", "calamares_romana"
        ],
    },
    "primavera": {
        "primero": [
            "ensalada_mixta", "ensalada_cesar", "ensalada_campera", "arroz_cubana",
            "paella", "macarrones", "macarrones_tomate", "crema_verduras",
            "judias_verdes", "arroz_tres_delicias"
        ],
        "segundo": [
            "pollo_plancha", "merluza_plancha", "pollo_asado", "albondigas",
            "hamburguesa", "bacalao_plancha", "tortilla_patata", "lomo_plancha"
        ],
    },
    "verano": {
        "primero": [
            "gazpacho", "salmorejo", "ensalada_mixta", "ensalada_cesar",
            "ensalada_pasta", "ensalada_arroz", "ensalada_campera",
            "arroz_tres_delicias", "paella", "macarrones_tomate"
        ],
        "segundo": [
            "merluza_plancha", "pollo_plancha", "hamburguesa", "bacalao_plancha",
            "tortilla_patata", "boquerones_fritos", "calamares_romana", "pollo_asado"
        ],
    },
    "otono": {
        "primero": [
            "lentejas", "crema_calabaza", "crema_verduras", "sopa_verduras",
            "macarrones_bolonesa", "arroz_pollo", "judias_verdes", "paella"
        ],
        "segundo": [
            "pollo_asado", "merluza_plancha", "albondigas", "filete_empanado",
            "chuletas_cerdo", "lomo_empanado", "carne_dia", "pescado_dia"
        ],
    },
}


# =========================================================
# CLIENTE SUPABASE
# =========================================================

def build_client() -> Client:
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)


# =========================================================
# CARGA DE DATOS REALES
# =========================================================

def fetch_restaurants(client: Client) -> list[dict[str, Any]]:
    res = client.table("restaurants").select("id,name").execute()
    return res.data or []

def fetch_users(client: Client) -> list[dict[str, Any]]:
    res = client.table("users").select("id,restaurant_id,role").execute()
    return res.data or []


def fetch_normal_users(client: Client) -> list[dict[str, Any]]:
    res = (
        client.table("users")
        .select("id,restaurant_id,role")
        .eq("role", "user")
        .execute()
    )
    return res.data or []


# =========================================================
# UTILIDADES DE NEGOCIO
# =========================================================

def dish_index(dishes: list[Dish]) -> dict[str, Dish]:
    return {d.canonical: d for d in dishes}


FIRST_INDEX = dish_index(FIRST_DISHES)
SECOND_INDEX = dish_index(SECOND_DISHES)


def choose_variant(dish: Dish) -> str:
    return random.choice(dish.variants)


def restaurant_popularity_factor() -> float:
    return random.uniform(0.85, 1.35)


def build_week_template_for_season(season: str) -> dict[str, dict[str, list[str]]]:
    """
    Devuelve una plantilla fija por temporada:
    {
      "lunes": {"primero": [...], "segundo": [...]},
      ...
    }
    """
    pool_first = SEASON_POOL[season]["primero"][:]
    pool_second = SEASON_POOL[season]["segundo"][:]

    random.shuffle(pool_first)
    random.shuffle(pool_second)

    weekdays = ["lunes", "martes", "miercoles", "jueves", "viernes"]
    template: dict[str, dict[str, list[str]]] = {}

    for i, wd in enumerate(weekdays):
        first_count = random.randint(*FIRSTS_PER_DAY)
        second_count = random.randint(*SECONDS_PER_DAY)

        # rotación simple para que la semana tenga patrón estable
        firsts = [pool_first[(i + j) % len(pool_first)] for j in range(first_count)]
        seconds = [pool_second[(i + j) % len(pool_second)] for j in range(second_count)]

        template[wd] = {
            "primero": firsts,
            "segundo": seconds,
        }

    return template


def maybe_swap_one_dish(dishes: list[str], pool: list[str], probability: float = 0.20) -> list[str]:
    """
    Pequeña variación semanal: a veces cambia 1 plato.
    """
    dishes = dishes[:]
    if random.random() < probability and dishes:
        idx = random.randrange(len(dishes))
        replacement = random.choice(pool)
        dishes[idx] = replacement
    # evitar duplicados en la misma lista manteniendo orden
    seen = set()
    unique = []
    for d in dishes:
        if d not in seen:
            seen.add(d)
            unique.append(d)
    return unique


def sold_units_for_dish(
    dish: Dish,
    restaurant_factor: float,
    season: str,
    weekday: str,
) -> int:
    base = dish.popularity * restaurant_factor

    # pequeños ajustes
    if weekday in ("jueves", "viernes"):
        base *= 1.08
    if season == "invierno" and dish.canonical in {"lentejas", "fabada", "cocido", "sopa_castellana"}:
        base *= 1.15
    if season == "verano" and dish.canonical in {"gazpacho", "salmorejo", "ensalada_mixta", "ensalada_cesar"}:
        base *= 1.12

    noise = random.uniform(0.85, 1.15)
    units = int(round(base * noise))
    return max(units, 6)


def generate_rating_values(dish: Dish, sold_units: int) -> list[int]:
    """
    Ratings 1-5. Más ventas tienden a un pelín mejor rating, pero con ruido.
    """
    num_ratings = random.randint(*RATINGS_PER_ITEM_RANGE)
    if num_ratings == 0:
        return []

    adjusted_base = dish.rating_base
    if sold_units > 45:
        adjusted_base += 0.1
    elif sold_units < 20:
        adjusted_base -= 0.1

    values = []
    for _ in range(num_ratings):
        value = round(random.gauss(adjusted_base, 0.55))
        value = max(1, min(5, int(value)))
        values.append(value)
    return values


# =========================================================
# GENERACIÓN PRINCIPAL
# =========================================================

def build_owner_map(users: list[dict[str, Any]]) -> dict[str, str | None]:
    """
    restaurant_id -> owner_user_id si existe
    """
    mapping: dict[str, str | None] = {}
    for user in users:
        rid = user.get("restaurant_id")
        if rid and user.get("role") == "owner":
            mapping[rid] = user["id"]
    return mapping


def generate_synthetic_payloads(
    restaurants: list[dict[str, Any]],
    owner_map: dict[str, str | None],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Devuelve payloads para:
    - menus
    - menu_items
    - menu_item_sales
    - ratings
    """
    menus_payload: list[dict[str, Any]] = []
    menu_items_payload: list[dict[str, Any]] = []
    sales_payload: list[dict[str, Any]] = []
    ratings_payload: list[dict[str, Any]] = []

    # plantilla fija por restaurante y temporada
    restaurant_templates: dict[str, dict[str, dict[str, dict[str, list[str]]]]] = {}
    restaurant_factors: dict[str, float] = {}

    for r in restaurants:
        rid = r["id"]
        restaurant_factors[rid] = restaurant_popularity_factor()
        restaurant_templates[rid] = {
            "invierno": build_week_template_for_season("invierno"),
            "primavera": build_week_template_for_season("primavera"),
            "verano": build_week_template_for_season("verano"),
            "otono": build_week_template_for_season("otono"),
        }

    for current_date in daterange(START_DATE, END_DATE):
        if not is_weekday(current_date):
            continue

        season = get_season(current_date)
        wd = weekday_name_es(current_date)

        for restaurant in restaurants:
            rid = restaurant["id"]
            owner_user_id = owner_map.get(rid)
            if not owner_user_id:
                # si no hay owner, saltamos para no romper images/uploaded_by si luego lo usáis
                # para menus y menu_items realmente no hace falta owner, así que seguimos
                pass

            template = restaurant_templates[rid][season][wd]

            first_pool = SEASON_POOL[season]["primero"]
            second_pool = SEASON_POOL[season]["segundo"]

            # pequeñas variaciones semanales
            chosen_firsts = maybe_swap_one_dish(template["primero"], first_pool, probability=0.18)
            chosen_seconds = maybe_swap_one_dish(template["segundo"], second_pool, probability=0.18)

            # construir menú
            menu_row = {
                "restaurant_id": rid,
                "date": current_date.isoformat(),
                "source_image_id": None,
                "raw_text": None,
                "parsed_json": None,
                "season_tag": season,
            }
            menus_payload.append(menu_row)

            # guardamos items “pendientes de enlazar” al menu_id real
            # luego haremos insert de menus y con los ids creamos los items
            menu_row["_synthetic_firsts"] = chosen_firsts
            menu_row["_synthetic_seconds"] = chosen_seconds
            menu_row["_restaurant_factor"] = restaurant_factors[rid]

    return menus_payload, menu_items_payload, sales_payload, ratings_payload


# =========================================================
# INSERTS
# =========================================================

def insert_menus_and_related(
    client: Client,
    menus_payload: list[dict[str, Any]],
    normal_users: list[dict[str, Any]],
) -> None:
    """
    Inserta menus y luego genera menu_items + sales + ratings
    aprovechando los ids reales devueltos por Supabase.
    """
    user_ids = [u["id"] for u in normal_users]
    if not user_ids and CREATE_RATINGS:
        print("No hay usuarios normales (role='user') en la tabla users; no se podrán crear ratings.")
        user_ids = []

    core_menu_rows = []
    synthetic_meta = []

    for m in menus_payload:
        meta = {
            "firsts": m.pop("_synthetic_firsts"),
            "seconds": m.pop("_synthetic_seconds"),
            "restaurant_factor": m.pop("_restaurant_factor"),
            "date": m["date"],
            "season": m["season_tag"],
            "restaurant_id": m["restaurant_id"],
        }
        synthetic_meta.append(meta)
        core_menu_rows.append(m)

    inserted_menus = []
    for batch in chunked(core_menu_rows, 200):
        if DRY_RUN:
            # ids fake si haces dry run
            fake = []
            for row in batch:
                fake.append({**row, "id": f"fake-{len(inserted_menus)+len(fake)+1}"})
            inserted_menus.extend(fake)
        else:
            res = client.table("menus").insert(batch).execute()
            inserted_menus.extend(res.data or [])

    all_menu_items = []
    all_sales = []
    all_ratings = []

    for inserted_menu, meta in zip(inserted_menus, synthetic_meta):
        menu_id = inserted_menu["id"]
        season = meta["season"]
        wd = weekday_name_es(datetime.fromisoformat(meta["date"]).date())
        restaurant_factor = meta["restaurant_factor"]

        # primeros
        for canonical in meta["firsts"]:
            dish = FIRST_INDEX[canonical]
            display_name = choose_variant(dish)
            item = {
                "menu_id": menu_id,
                "name": display_name,
                "description": None,
                "price": None,
                "tags": None,
                "predicted": False,
                "normalized_name": None,  # lo rellena luego vuestro script
                "category": None,         # lo rellena luego vuestro script
            }
            all_menu_items.append((item, dish, season, wd, restaurant_factor))

        # segundos
        for canonical in meta["seconds"]:
            dish = SECOND_INDEX[canonical]
            display_name = choose_variant(dish)
            item = {
                "menu_id": menu_id,
                "name": display_name,
                "description": None,
                "price": None,
                "tags": None,
                "predicted": False,
                "normalized_name": None,
                "category": None,
            }
            all_menu_items.append((item, dish, season, wd, restaurant_factor))

    inserted_menu_items = []
    menu_item_rows = [x[0] for x in all_menu_items]

    for batch in chunked(menu_item_rows, 500):
        if DRY_RUN:
            fake = []
            for row in batch:
                fake.append({**row, "id": f"fake-item-{len(inserted_menu_items)+len(fake)+1}"})
            inserted_menu_items.extend(fake)
        else:
            res = client.table("menu_items").insert(batch).execute()
            inserted_menu_items.extend(res.data or [])

    for inserted_item, (_, dish, season, wd, restaurant_factor) in zip(inserted_menu_items, all_menu_items):
        sold_units = sold_units_for_dish(dish, restaurant_factor, season, wd)
        all_sales.append(
            {
                "menu_item_id": inserted_item["id"],
                "sold_units": sold_units,
                "sale_date": datetime.now().date().isoformat(),
            }
        )

        if CREATE_RATINGS and user_ids:
            rating_values = generate_rating_values(dish, sold_units)
            chosen_users = random.sample(user_ids, k=min(len(user_ids), len(rating_values))) if rating_values else []

            for value, user_id in zip(rating_values, chosen_users):
                all_ratings.append(
                    {
                        "user_id": user_id,
                        "menu_item_id": inserted_item["id"],
                        "rating": value,
                        "comment": None,
                    }
                )

    for batch in chunked(all_sales, 500):
        if not DRY_RUN:
            client.table("menu_item_sales").insert(batch).execute()

    if CREATE_RATINGS and all_ratings:
        for batch in chunked(all_ratings, 500):
            if not DRY_RUN:
                client.table("ratings").insert(batch).execute()

    print(f"Menús insertados: {len(inserted_menus)}")
    print(f"Platos insertados: {len(inserted_menu_items)}")
    print(f"Ventas insertadas: {len(all_sales)}")
    if CREATE_RATINGS:
        print(f"Ratings insertados: {len(all_ratings)}")


# =========================================================
# MAIN
# =========================================================

def main() -> None:
    random.seed(42)

    client = build_client()

    restaurants = fetch_restaurants(client)
    users = fetch_users(client)
    normal_users = fetch_normal_users(client)

    if not restaurants:
        print("No hay restaurantes en la tabla restaurants.")
        return

    owner_map = build_owner_map(users)

    menus_payload, _, _, _ = generate_synthetic_payloads(restaurants, owner_map)

    print(f"Se van a generar {len(menus_payload)} menús sintéticos.")
    print(f"Usuarios normales disponibles para ratings: {len(normal_users)}")

    insert_menus_and_related(client, menus_payload, normal_users)


if __name__ == "__main__":
    main()