#!/usr/bin/env python3
"""
normalize_menu_items.py

Lee los platos de Supabase desde public.menu_items, limpia el texto,
normaliza nombres de platos y asigna category = primero | segundo.

Requisitos:
    pip install supabase python-dotenv Unidecode

Variables de entorno necesarias:
    SUPABASE_URL=...
    SUPABASE_SERVICE_ROLE_KEY=...

Uso:
    python normalize_menu_items.py

Notas:
- Usa la service role key porque hace updates.
- Si una fila no se puede resolver, la deja con normalized_name/category en NULL
  y la añade al listado de pendientes.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client
from unidecode import unidecode


# ---------------------------------------------------------
# Config
# ---------------------------------------------------------

BATCH_SIZE = 500
DRY_RUN = False  # Ponlo a True si quieres probar sin hacer updates


# ---------------------------------------------------------
# Patrones de ruido / exclusión
# ---------------------------------------------------------

INVALID_PATTERNS = [
    "incluye pan",
    "pan y bebida",
    "bebida incluida",
    "vino y gaseosa",
    "agua y vino",
    "postre o cafe",
    "postre o café",
    "menu del dia",
    "menú del día",
    "a elegir",
    "primer plato",
    "segundo plato",
    "primeros a elegir",
    "segundos a elegir",
    "cafe",
    "café",
]

# Si quieres, puedes filtrar también platos demasiado genéricos o basura OCR
TOO_GENERIC_PATTERNS = [
    "varios",
    "surtido",
    "especialidad",
]


# ---------------------------------------------------------
# Diccionario de normalización
# Clave = texto limpio
# Valor = nombre canónico
# ---------------------------------------------------------

NORMALIZATION_MAP: dict[str, str] = {
    # Primeros
    "lentejas": "lentejas",
    "lentejas caseras": "lentejas",
    "lentejas estofadas": "lentejas",
    "lentejas guisadas": "lentejas",
    "fabada": "fabada",
    "fabada asturiana": "fabada",
    "cocido": "cocido",
    "cocido madrileno": "cocido",
    "cocido madrileño": "cocido",
    "garbanzos": "garbanzos",
    "garbanzos guisados": "garbanzos",
    "judias verdes": "judias_verdes",
    "judias verdes con jamon": "judias_verdes",
    "judias verdes con jamón": "judias_verdes",
    "sopa castellana": "sopa_castellana",
    "sopa de cocido": "sopa_cocido",
    "sopa de verduras": "sopa_verduras",
    "crema de verduras": "crema_verduras",
    "crema de calabaza": "crema_calabaza",
    "crema de calabacin": "crema_calabacin",
    "crema de calabacín": "crema_calabacin",
    "ensalada mixta": "ensalada_mixta",
    "ensalada cesar": "ensalada_cesar",
    "ensalada césar": "ensalada_cesar",
    "ensalada de pasta": "ensalada_pasta",
    "ensalada campera": "ensalada_campera",
    "ensalada de arroz": "ensalada_arroz",
    "arroz a la cubana": "arroz_cubana",
    "arroz tres delicias": "arroz_tres_delicias",
    "paella": "paella",
    "paella mixta": "paella",
    "arroz con pollo": "arroz_pollo",
    "macarrones": "macarrones",
    "macarrones con tomate": "macarrones_tomate",
    "macarrones a la bolonesa": "macarrones_bolonesa",
    "macarrones a la boloñesa": "macarrones_bolonesa",
    "macarrones boloñesa": "macarrones_bolonesa",
    "macarrones bolonesa": "macarrones_bolonesa",
    "pasta boloñesa": "macarrones_bolonesa",
    "espaguetis carbonara": "espaguetis_carbonara",
    "espaguetis a la carbonara": "espaguetis_carbonara",
    "espaguetis boloñesa": "espaguetis_bolonesa",
    "espaguetis a la boloñesa": "espaguetis_bolonesa",
    "pasta del dia": "pasta_dia",
    "pasta del día": "pasta_dia",
    "pure de verduras": "pure_verduras",
    "puré de verduras": "pure_verduras",
    "gazpacho": "gazpacho",
    "salmorejo": "salmorejo",
    # Segundos
    "merluza a la plancha": "merluza_plancha",
    "merluza plancha": "merluza_plancha",
    "filete de merluza a la plancha": "merluza_plancha",
    "merluza rebozada": "merluza_rebozada",
    "bacalao": "bacalao",
    "bacalao a la plancha": "bacalao_plancha",
    "pollo asado": "pollo_asado",
    "pollo al horno": "pollo_asado",
    "pollo empanado": "pollo_empanado",
    "filete de pollo empanado": "pollo_empanado",
    "pechuga de pollo a la plancha": "pollo_plancha",
    "pollo a la plancha": "pollo_plancha",
    "filete de ternera": "filete_ternera",
    "ternera a la plancha": "ternera_plancha",
    "escalope de ternera": "escalope_ternera",
    "filete empanado": "filete_empanado",
    "secreto iberico": "secreto_iberico",
    "secreto ibérico": "secreto_iberico",
    "costillas al horno": "costillas_horno",
    "chuletas de cerdo": "chuletas_cerdo",
    "lomo a la plancha": "lomo_plancha",
    "lomo empanado": "lomo_empanado",
    "albondigas": "albondigas",
    "albóndigas": "albondigas",
    "albondigas en salsa": "albondigas",
    "albóndigas en salsa": "albondigas",
    "hamburguesa": "hamburguesa",
    "hamburguesa completa": "hamburguesa",
    "tortilla de patata": "tortilla_patata",
    "revuelto de setas": "revuelto_setas",
    "calamares a la romana": "calamares_romana",
    "boquerones fritos": "boquerones_fritos",
    "pescado del dia": "pescado_dia",
    "pescado del día": "pescado_dia",
    "carne del dia": "carne_dia",
    "carne del día": "carne_dia",
}


# ---------------------------------------------------------
# Categorías por nombre canónico
# ---------------------------------------------------------

CATEGORY_MAP: dict[str, str] = {
    # Primeros
    "lentejas": "primero",
    "fabada": "primero",
    "cocido": "primero",
    "garbanzos": "primero",
    "judias_verdes": "primero",
    "sopa_castellana": "primero",
    "sopa_cocido": "primero",
    "sopa_verduras": "primero",
    "crema_verduras": "primero",
    "crema_calabaza": "primero",
    "crema_calabacin": "primero",
    "ensalada_mixta": "primero",
    "ensalada_cesar": "primero",
    "ensalada_pasta": "primero",
    "ensalada_campera": "primero",
    "ensalada_arroz": "primero",
    "arroz_cubana": "primero",
    "arroz_tres_delicias": "primero",
    "paella": "primero",
    "arroz_pollo": "primero",
    "macarrones": "primero",
    "macarrones_tomate": "primero",
    "macarrones_bolonesa": "primero",
    "espaguetis_carbonara": "primero",
    "espaguetis_bolonesa": "primero",
    "pasta_dia": "primero",
    "pure_verduras": "primero",
    "gazpacho": "primero",
    "salmorejo": "primero",
    # Segundos
    "merluza_plancha": "segundo",
    "merluza_rebozada": "segundo",
    "bacalao": "segundo",
    "bacalao_plancha": "segundo",
    "pollo_asado": "segundo",
    "pollo_empanado": "segundo",
    "pollo_plancha": "segundo",
    "filete_ternera": "segundo",
    "ternera_plancha": "segundo",
    "escalope_ternera": "segundo",
    "filete_empanado": "segundo",
    "secreto_iberico": "segundo",
    "costillas_horno": "segundo",
    "chuletas_cerdo": "segundo",
    "lomo_plancha": "segundo",
    "lomo_empanado": "segundo",
    "albondigas": "segundo",
    "hamburguesa": "segundo",
    "tortilla_patata": "segundo",
    "revuelto_setas": "segundo",
    "calamares_romana": "segundo",
    "boquerones_fritos": "segundo",
    "pescado_dia": "segundo",
    "carne_dia": "segundo",
}


# ---------------------------------------------------------
# Reglas fallback por keywords
# ---------------------------------------------------------

FIRST_KEYWORDS = [
    "ensalada",
    "crema",
    "sopa",
    "lentejas",
    "garbanzos",
    "judias",
    "judías",
    "macarrones",
    "espaguetis",
    "pasta",
    "arroz",
    "gazpacho",
    "salmorejo",
    "pure",
    "puré",
    "cocido",
    "fabada",
]

SECOND_KEYWORDS = [
    "pollo",
    "merluza",
    "ternera",
    "filete",
    "bacalao",
    "costillas",
    "secreto",
    "pescado",
    "carne",
    "hamburguesa",
    "albondigas",
    "albóndigas",
    "calamares",
    "boquerones",
    "chuletas",
    "lomo",
    "tortilla",
    "revuelto",
]


# ---------------------------------------------------------
# Utilidades
# ---------------------------------------------------------

def clean_text(value: str | None) -> str:
    if not value:
        return ""

    text = value.strip().lower()
    text = unidecode(text)

    # Separadores comunes
    text = text.replace("/", " ")
    text = text.replace("-", " ")
    text = text.replace("_", " ")

    # Quitar contenido entre paréntesis
    text = re.sub(r"\(.*?\)", " ", text)

    # Quitar signos raros
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Espacios múltiples
    text = re.sub(r"\s+", " ", text).strip()

    return text


def is_invalid_item(cleaned_name: str) -> bool:
    if not cleaned_name:
        return True

    for pattern in INVALID_PATTERNS:
        if pattern in cleaned_name:
            return True

    for pattern in TOO_GENERIC_PATTERNS:
        if cleaned_name == pattern:
            return True

    return False


def normalize_name(cleaned_name: str) -> str | None:
    if not cleaned_name or is_invalid_item(cleaned_name):
        return None

    # 1) Match exacto en diccionario
    if cleaned_name in NORMALIZATION_MAP:
        return NORMALIZATION_MAP[cleaned_name]

    # 2) Heurísticas simples para variantes comunes
    # Lentejas
    if "lentejas" in cleaned_name:
        return "lentejas"

    # Macarrones boloñesa
    if "macarrones" in cleaned_name and ("bolonesa" in cleaned_name or "bolonesa" in cleaned_name or "bolo" in cleaned_name):
        return "macarrones_bolonesa"

    # Ensaladas
    if "ensalada mixta" in cleaned_name:
        return "ensalada_mixta"
    if "ensalada cesar" in cleaned_name:
        return "ensalada_cesar"
    if "ensalada" in cleaned_name:
        return "ensalada_mixta"

    # Cremas
    if "crema" in cleaned_name and "calabaza" in cleaned_name:
        return "crema_calabaza"
    if "crema" in cleaned_name and "calabacin" in cleaned_name:
        return "crema_calabacin"
    if "crema" in cleaned_name:
        return "crema_verduras"

    # Sopas
    if "sopa castellana" in cleaned_name:
        return "sopa_castellana"
    if "sopa" in cleaned_name and "verduras" in cleaned_name:
        return "sopa_verduras"
    if "sopa" in cleaned_name:
        return "sopa_verduras"

    # Arroces / pasta
    if "paella" in cleaned_name:
        return "paella"
    if "arroz" in cleaned_name and "cubana" in cleaned_name:
        return "arroz_cubana"
    if "arroz" in cleaned_name and "pollo" in cleaned_name:
        return "arroz_pollo"
    if "arroz" in cleaned_name and "tres delicias" in cleaned_name:
        return "arroz_tres_delicias"
    if "macarrones" in cleaned_name and "tomate" in cleaned_name:
        return "macarrones_tomate"
    if "macarrones" in cleaned_name:
        return "macarrones"
    if "espaguetis" in cleaned_name and "carbonara" in cleaned_name:
        return "espaguetis_carbonara"
    if "espaguetis" in cleaned_name and ("bolonesa" in cleaned_name or "bolo" in cleaned_name):
        return "espaguetis_bolonesa"

    # Segundos
    if "merluza" in cleaned_name and "plancha" in cleaned_name:
        return "merluza_plancha"
    if "merluza" in cleaned_name and "rebozada" in cleaned_name:
        return "merluza_rebozada"
    if "merluza" in cleaned_name:
        return "merluza_plancha"

    if "bacalao" in cleaned_name and "plancha" in cleaned_name:
        return "bacalao_plancha"
    if "bacalao" in cleaned_name:
        return "bacalao"

    if "pollo" in cleaned_name and "empanado" in cleaned_name:
        return "pollo_empanado"
    if "pollo" in cleaned_name and "plancha" in cleaned_name:
        return "pollo_plancha"
    if "pollo" in cleaned_name and ("asado" in cleaned_name or "horno" in cleaned_name):
        return "pollo_asado"
    if "pollo" in cleaned_name:
        return "pollo_plancha"

    if "albondigas" in cleaned_name:
        return "albondigas"

    if "hamburguesa" in cleaned_name:
        return "hamburguesa"

    if "ternera" in cleaned_name and "plancha" in cleaned_name:
        return "ternera_plancha"
    if "filete de ternera" in cleaned_name:
        return "filete_ternera"
    if "escalope" in cleaned_name:
        return "escalope_ternera"

    if "secreto" in cleaned_name:
        return "secreto_iberico"

    if "costillas" in cleaned_name:
        return "costillas_horno"

    if "chuletas" in cleaned_name:
        return "chuletas_cerdo"

    if "lomo" in cleaned_name and "empanado" in cleaned_name:
        return "lomo_empanado"
    if "lomo" in cleaned_name:
        return "lomo_plancha"

    if "calamares" in cleaned_name:
        return "calamares_romana"

    if "boquerones" in cleaned_name:
        return "boquerones_fritos"

    if "tortilla de patata" in cleaned_name:
        return "tortilla_patata"

    if "revuelto" in cleaned_name:
        return "revuelto_setas"

    if "pescado" in cleaned_name:
        return "pescado_dia"

    if "carne" in cleaned_name:
        return "carne_dia"

    return None


def infer_category(cleaned_name: str, normalized_name: str | None) -> str | None:
    if normalized_name and normalized_name in CATEGORY_MAP:
        return CATEGORY_MAP[normalized_name]

    if not cleaned_name:
        return None

    for keyword in FIRST_KEYWORDS:
        if keyword in cleaned_name:
            return "primero"

    for keyword in SECOND_KEYWORDS:
        if keyword in cleaned_name:
            return "segundo"

    return None


def build_client() -> Client:
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en el entorno.", file=sys.stderr)
        sys.exit(1)

    return create_client(url, key)


def fetch_menu_items(client: Client) -> list[dict[str, Any]]:
    """
    Descarga todos los menu_items con paginación.
    """
    all_rows: list[dict[str, Any]] = []
    start = 0

    while True:
        end = start + BATCH_SIZE - 1
        response = (
            client.table("menu_items")
            .select("id,name,normalized_name,category")
            .range(start, end)
            .execute()
        )

        rows = response.data or []
        if not rows:
            break

        all_rows.extend(rows)

        if len(rows) < BATCH_SIZE:
            break

        start += BATCH_SIZE

    return all_rows


def update_menu_item(
    client: Client,
    item_id: str,
    normalized_name: str | None,
    category: str | None,
) -> None:
    payload = {
        "normalized_name": normalized_name,
        "category": category,
    }

    if DRY_RUN:
        return

    client.table("menu_items").update(payload).eq("id", item_id).execute()


def main() -> None:
    client = build_client()

    print("Descargando menu_items...")
    rows = fetch_menu_items(client)
    print(f"Total filas: {len(rows)}")

    unresolved: list[dict[str, str]] = []
    changed = 0
    skipped_invalid = 0

    for row in rows:
        item_id = row["id"]
        original_name = row.get("name") or ""
        current_normalized = row.get("normalized_name")
        current_category = row.get("category")

        cleaned = clean_text(original_name)

        if is_invalid_item(cleaned):
            skipped_invalid += 1
            # Si quieres limpiar basura también en BD, descomenta:
            # update_menu_item(client, item_id, None, None)
            continue

        normalized = normalize_name(cleaned)
        category = infer_category(cleaned, normalized)

        if normalized is None or category is None:
            unresolved.append(
                {
                    "id": item_id,
                    "name": original_name,
                    "cleaned": cleaned,
                    "normalized_name": normalized or "",
                    "category": category or "",
                }
            )
            continue

        if normalized != current_normalized or category != current_category:
            update_menu_item(client, item_id, normalized, category)
            changed += 1
            print(f"Actualizado: {original_name!r} -> {normalized} ({category})")

    print("\n--- Resumen ---")
    print(f"Total filas procesadas: {len(rows)}")
    print(f"Actualizadas: {changed}")
    print(f"Ignoradas por ruido: {skipped_invalid}")
    print(f"No resueltas: {len(unresolved)}")

    if unresolved:
        print("\n--- Casos no resueltos ---")
        for item in unresolved[:100]:
            print(f"- {item['name']}  | cleaned={item['cleaned']}")
        print("\nConsejo: añade estos casos al NORMALIZATION_MAP o mejora heurísticas.")


if __name__ == "__main__":
    main()