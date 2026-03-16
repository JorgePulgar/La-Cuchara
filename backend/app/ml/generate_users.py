#!/usr/bin/env python3
"""
generate_test_users.py

Genera usuarios normales de prueba en Supabase.

Hace:
- crea usuarios en auth.users usando Auth Admin
- inserta filas en public.users con role='user'
- restaurant_id = NULL

Requisitos:
    pip install supabase python-dotenv

Variables de entorno:
    SUPABASE_URL=...
    SUPABASE_SERVICE_ROLE_KEY=...

Uso:
    python generate_test_users.py
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

NUM_USERS = 20
DRY_RUN = False
RANDOM_SEED = 42
EMAIL_DOMAIN = "lacuchara-users.local"
DEFAULT_USER_PASSWORD = "UserDemo123!"
AUTO_CONFIRM_EMAIL = True


# =========================================================
# DATOS SINTÉTICOS
# =========================================================

FIRST_NAMES = [
    "Ana", "Luis", "Marta", "Carlos", "Lucia", "Javier", "Elena", "Pablo",
    "Sara", "David", "Irene", "Alvaro", "Nuria", "Sergio", "Andrea", "Miguel",
    "Raquel", "Diego", "Beatriz", "Mario", "Cristina", "Alberto", "Paula",
    "Hugo", "Alicia", "Ivan", "Patricia", "Adrian", "Claudia", "Ruben",
]

LAST_NAMES = [
    "Garcia", "Martinez", "Lopez", "Sanchez", "Perez", "Gomez", "Martin",
    "Jimenez", "Ruiz", "Hernandez", "Diaz", "Moreno", "Muñoz", "Alvarez",
    "Romero", "Navarro", "Torres", "Dominguez", "Vazquez", "Ramos",
]


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

def slugify(text: str) -> str:
    allowed = string.ascii_lowercase + string.digits
    text = text.lower().replace("á", "a").replace("é", "e").replace("í", "i")
    text = text.replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    text = "".join(ch if ch.isalnum() else "_" for ch in text)
    text = "_".join(part for part in text.split("_") if part)
    text = "".join(ch for ch in text if ch in allowed or ch == "_")
    return text.strip("_")


def build_full_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def build_email(full_name: str, index: int, existing_emails: set[str]) -> str:
    base = slugify(full_name)
    candidate = f"{base}_{index}@{EMAIL_DOMAIN}"
    n = 2
    while candidate in existing_emails:
        candidate = f"{base}_{index}_{n}@{EMAIL_DOMAIN}"
        n += 1
    existing_emails.add(candidate)
    return candidate


# =========================================================
# SUPABASE LECTURA
# =========================================================

def fetch_existing_public_user_emails(client: Client) -> set[str]:
    res = client.table("users").select("email").execute()
    rows = res.data or []
    return {row["email"] for row in rows if row.get("email")}


# =========================================================
# CREACIÓN AUTH + PUBLIC.USERS
# =========================================================

def create_auth_user(client: Client, email: str, password: str) -> dict[str, Any]:
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
                "role": "user",
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
        "role": "user",
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
# MAIN
# =========================================================

def main() -> None:
    random.seed(RANDOM_SEED)

    client = build_client()
    existing_emails = fetch_existing_public_user_emails(client)

    print(f"Emails existentes en public.users: {len(existing_emails)}")

    created_summary: list[dict[str, str]] = []

    for i in range(1, NUM_USERS + 1):
        full_name = build_full_name()
        email = build_email(full_name, i, existing_emails)

        auth_user = create_auth_user(
            client=client,
            email=email,
            password=DEFAULT_USER_PASSWORD,
        )

        public_user = insert_public_user(
            client=client,
            user_id=auth_user["id"],
            email=auth_user["email"],
        )

        created_summary.append(
            {
                "name": full_name,
                "email": auth_user["email"],
                "user_id": public_user["id"],
            }
        )

        print(f"[{i}/{NUM_USERS}] OK -> {full_name} | {auth_user['email']}")

    print("\nResumen final:")
    for row in created_summary[:10]:
        print(f"- {row['name']} | {row['email']} | id={row['user_id']}")

    print(f"\nTotal creados: {len(created_summary)}")
    if not DRY_RUN:
        print(f"Password por defecto: {DEFAULT_USER_PASSWORD}")


if __name__ == "__main__":
    main()