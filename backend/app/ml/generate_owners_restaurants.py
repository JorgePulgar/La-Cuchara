#!/usr/bin/env python3
"""
generate_restaurants_with_owners.py

Genera restaurantes sintéticos y sus usuarios owner correspondientes
compatibles con el esquema actual de Supabase.

Qué hace:
- crea usuarios reales en auth.users usando Auth Admin
- inserta esos usuarios en public.users
- crea restaurantes en public.restaurants
- enlaza:
    restaurants.owner_user_id -> public.users.id
    public.users.restaurant_id -> public.restaurants.id

Requisitos:
    pip install supabase python-dotenv

Variables de entorno:
    SUPABASE_URL=...
    SUPABASE_SERVICE_ROLE_KEY=...

Uso:
    python generate_restaurants_with_owners.py
"""

from __future__ import annotations

import os
import random
import string
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client


# =========================================================
# CONFIG
# =========================================================

NUM_RESTAURANTS = 15
DRY_RUN = False
RANDOM_SEED = 42
EMAIL_DOMAIN = "lacuchara-demo.local"
DEFAULT_OWNER_PASSWORD = "OwnerDemo123!"
AUTO_CONFIRM_EMAIL = True


# =========================================================
# DATOS SINTÉTICOS
# =========================================================

NAME_PREFIXES = [
    "La",
    "El",
    "Casa",
    "Mesón",
    "Bar",
    "Restaurante",
    "Taberna",
    "Rincón",
    "Asador",
    "Bodega",
]

NAME_MIDDLES = [
    "Cuchara",
    "Encina",
    "Parra",
    "Sartén",
    "Abuela",
    "Fogón",
    "Olivo",
    "Plaza",
    "Mercado",
    "Puchero",
    "Caldero",
    "Brasa",
    "Huerta",
    "Puerto",
]

NAME_SUFFIXES = [
    "",
    "de Madrid",
    "Castizo",
    "del Barrio",
    "Tradicional",
    "Moderno",
    "de la Plaza",
    "del Centro",
    "Norte",
    "Sur",
]

STREETS = [
    "Calle Mayor",
    "Gran Vía",
    "Calle Alcalá",
    "Paseo de la Castellana",
    "Calle Princesa",
    "Calle Goya",
    "Calle Serrano",
    "Calle Atocha",
    "Calle Velázquez",
    "Calle Orense",
    "Calle Raimundo Fernández Villaverde",
    "Calle Bravo Murillo",
]

PHONE_PREFIX = "+34 91"

LAT_RANGE = (40.3800, 40.4900)
LON_RANGE = (-3.7500, -3.6500)


# =========================================================
# CLIENTE
# =========================================================

def build_client() -> Client:
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY")

    return create_client(url, key)


# =========================================================
# HELPERS
# =========================================================

def random_phone() -> str:
    a = random.randint(100, 999)
    b = random.randint(10, 99)
    c = random.randint(10, 99)
    return f"{PHONE_PREFIX} {a} {b} {c}"


def random_address() -> str:
    street = random.choice(STREETS)
    number = random.randint(1, 180)
    return f"{street}, {number}, Madrid"


def random_lat_lon() -> tuple[float, float]:
    lat = round(random.uniform(*LAT_RANGE), 6)
    lon = round(random.uniform(*LON_RANGE), 6)
    return lat, lon


def slugify(text: str) -> str:
    allowed = string.ascii_lowercase + string.digits
    text = text.lower().replace("á", "a").replace("é", "e").replace("í", "i")
    text = text.replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    text = "".join(ch if ch.isalnum() else "_" for ch in text)
    text = "_".join(part for part in text.split("_") if part)
    text = "".join(ch for ch in text if ch in allowed or ch == "_")
    return text.strip("_")


def build_restaurant_name(existing_names: set[str]) -> str:
    while True:
        prefix = random.choice(NAME_PREFIXES)
        middle = random.choice(NAME_MIDDLES)
        suffix = random.choice(NAME_SUFFIXES)

        name = f"{prefix} {middle} {suffix}".strip()
        name = " ".join(name.split())

        if name not in existing_names:
            existing_names.add(name)
            return name


def build_owner_email(restaurant_name: str, existing_emails: set[str], index: int) -> str:
    base = slugify(restaurant_name)
    candidate = f"owner_{base}_{index}@{EMAIL_DOMAIN}"
    n = 2
    while candidate in existing_emails:
        candidate = f"owner_{base}_{index}_{n}@{EMAIL_DOMAIN}"
        n += 1
    existing_emails.add(candidate)
    return candidate


def chunked(seq: list[dict[str, Any]], size: int):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


# =========================================================
# SUPABASE LECTURA
# =========================================================

def fetch_existing_restaurant_names(client: Client) -> set[str]:
    res = client.table("restaurants").select("name").execute()
    rows = res.data or []
    return {row["name"] for row in rows if row.get("name")}


def fetch_existing_public_user_emails(client: Client) -> set[str]:
    res = client.table("users").select("email").execute()
    rows = res.data or []
    return {row["email"] for row in rows if row.get("email")}


# =========================================================
# CREACIÓN AUTH + PUBLIC.USERS
# =========================================================

def create_auth_owner_user(client: Client, email: str, password: str) -> dict[str, Any]:
    """
    Crea un usuario real en auth.users usando Supabase Auth Admin.
    """
    if DRY_RUN:
        fake_id = f"fake-auth-user-{slugify(email)}"
        return {"id": fake_id, "email": email}

    response = client.auth.admin.create_user(
        {
            "email": email,
            "password": password,
            "email_confirm": AUTO_CONFIRM_EMAIL,
            "user_metadata": {
                "seeded": True,
                "role": "owner",
            },
        }
    )

    user = getattr(response, "user", None)
    if user is None:
        raise RuntimeError(f"No se pudo crear auth user para {email}")

    return {
        "id": user.id,
        "email": user.email,
    }


def insert_public_user(client: Client, user_id: str, email: str) -> dict[str, Any]:
    payload = {
        "id": user_id,
        "email": email,
        "role": "owner",
        "restaurant_id": None,
    }

    if DRY_RUN:
        return payload

    res = client.table("users").insert(payload).execute()
    data = res.data or []
    if not data:
        raise RuntimeError(f"No se pudo insertar public.users para {email}")
    return data[0]


# =========================================================
# CREACIÓN RESTAURANTES
# =========================================================

def insert_restaurant(
    client: Client,
    *,
    name: str,
    address: str,
    lat: float,
    lon: float,
    phone: str,
    owner_user_id: str,
) -> dict[str, Any]:
    payload = {
        "name": name,
        "address": address,
        "lat": lat,
        "lon": lon,
        "phone": phone,
        "owner_user_id": owner_user_id,
    }

    if DRY_RUN:
        return {
            "id": f"fake-restaurant-{slugify(name)}",
            **payload,
        }

    res = client.table("restaurants").insert(payload).execute()
    data = res.data or []
    if not data:
        raise RuntimeError(f"No se pudo insertar restaurante {name}")
    return data[0]


def link_user_to_restaurant(client: Client, user_id: str, restaurant_id: str) -> None:
    if DRY_RUN:
        return

    client.table("users").update({"restaurant_id": restaurant_id}).eq("id", user_id).execute()


# =========================================================
# MAIN
# =========================================================

def main() -> None:
    random.seed(RANDOM_SEED)

    client = build_client()

    existing_names = fetch_existing_restaurant_names(client)
    existing_emails = fetch_existing_public_user_emails(client)

    print(f"Restaurantes existentes: {len(existing_names)}")
    print(f"Emails existentes en public.users: {len(existing_emails)}")

    created_summary: list[dict[str, str]] = []

    for i in range(1, NUM_RESTAURANTS + 1):
        restaurant_name = build_restaurant_name(existing_names)
        email = build_owner_email(restaurant_name, existing_emails, i)

        auth_user = create_auth_owner_user(
            client=client,
            email=email,
            password=DEFAULT_OWNER_PASSWORD,
        )

        public_user = insert_public_user(
            client=client,
            user_id=auth_user["id"],
            email=auth_user["email"],
        )

        lat, lon = random_lat_lon()
        restaurant = insert_restaurant(
            client=client,
            name=restaurant_name,
            address=random_address(),
            lat=lat,
            lon=lon,
            phone=random_phone(),
            owner_user_id=public_user["id"],
        )

        link_user_to_restaurant(
            client=client,
            user_id=public_user["id"],
            restaurant_id=restaurant["id"],
        )

        created_summary.append(
            {
                "restaurant_name": restaurant_name,
                "restaurant_id": restaurant["id"],
                "owner_email": auth_user["email"],
                "owner_user_id": public_user["id"],
            }
        )

        print(
            f"[{i}/{NUM_RESTAURANTS}] OK -> "
            f"{restaurant_name} | {auth_user['email']}"
        )

    print("\nResumen final:")
    for row in created_summary[:10]:
        print(
            f"- {row['restaurant_name']} | "
            f"owner={row['owner_email']} | "
            f"restaurant_id={row['restaurant_id']}"
        )

    print(f"\nTotal creados: {len(created_summary)}")
    if not DRY_RUN:
        print(f"Password por defecto de los owners: {DEFAULT_OWNER_PASSWORD}")


if __name__ == "__main__":
    main()