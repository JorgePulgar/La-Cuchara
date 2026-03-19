"""
backend/app/services/geocoding_service.py
Converts an address string into (lat, lon) coordinates using OpenStreetMap Nominatim.
Falls back to (None, None) on any error.
"""

import httpx

# Nominatim requires a descriptive User-Agent (usage policy)
_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_USER_AGENT = "LaCuchara/0.1 (development)"


async def geocode_address(address: str) -> tuple[float | None, float | None]:
    """
    Geocodes an address string using OpenStreetMap Nominatim.

    Returns:
        (lat, lon) tuple with float values, or (None, None) on failure.
    """
    if not address or not address.strip():
        return (None, None)

    params = {
        "q": address.strip(),
        "format": "json",
        "limit": 1,
    }

    headers = {
        "User-Agent": _USER_AGENT,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                _NOMINATIM_URL,
                params=params,
                headers=headers,
            )
            response.raise_for_status()

            results = response.json()

            if not results:
                return (None, None)

            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            return (lat, lon)

    except (httpx.HTTPError, KeyError, ValueError, IndexError) as e:
        # Log but don't crash — coordinates are non-critical
        print(f"[Geocoding] Failed to geocode '{address}': {e}")
        return (None, None)
