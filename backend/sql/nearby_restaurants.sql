-- =============================================================================
-- Haversine distance function for finding nearby restaurants
-- Run this in the Supabase SQL Editor to create the function.
-- =============================================================================

CREATE OR REPLACE FUNCTION get_nearby_restaurants(
    user_lat DOUBLE PRECISION,
    user_lon DOUBLE PRECISION,
    radius_km DOUBLE PRECISION DEFAULT 5.0
)
RETURNS TABLE (
    id UUID,
    name TEXT,
    address TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    phone TEXT,
    owner_user_id UUID,
    distance_km DOUBLE PRECISION
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        sub.id,
        sub.name,
        sub.address,
        sub.lat,
        sub.lon,
        sub.phone,
        sub.owner_user_id,
        sub.distance_km
    FROM (
        SELECT
            r.id,
            r.name,
            r.address,
            r.lat,
            r.lon,
            r.phone,
            r.owner_user_id,
            (
                6371 * acos(
                    LEAST(1.0, GREATEST(-1.0,
                        cos(radians(user_lat))
                        * cos(radians(r.lat))
                        * cos(radians(r.lon) - radians(user_lon))
                        + sin(radians(user_lat))
                        * sin(radians(r.lat))
                    ))
                )
            ) AS distance_km
        FROM restaurants r
        WHERE r.lat IS NOT NULL
          AND r.lon IS NOT NULL
    ) sub
    WHERE sub.distance_km <= radius_km
    ORDER BY sub.distance_km ASC;
$$;

COMMENT ON FUNCTION get_nearby_restaurants IS 'Returns restaurants within a given radius (km) from a point, using the Haversine formula. Results are ordered by distance ascending.';
