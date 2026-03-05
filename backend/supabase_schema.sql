-- =============================================================================
-- La Cuchara — Supabase SQL Schema
-- =============================================================================
-- This file defines all database tables for the La Cuchara platform.
-- Run this in the Supabase SQL Editor to create the schema.
--
-- Tables (8 total):
--   1. restaurants  — restaurant profiles
--   2. users        — application users (references auth.users)
--   3. menus        — daily/weekly menus per restaurant
--   4. menu_items   — individual dishes within a menu
--   5. images       — uploaded images (menu photos, etc.)
--   6. ratings      — user ratings and comments on menu items
--   7. visits       — user visit history to restaurants
--   8. predictions  — ML-generated menu predictions (future phase)
--
-- Note: "restaurants" is created before "users" because users.restaurant_id
-- references restaurants.id.
-- =============================================================================


-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- =============================================================================
-- 1. RESTAURANTS
-- Stores restaurant profiles. Created first because users may reference it.
-- =============================================================================
CREATE TABLE IF NOT EXISTS restaurants (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    name            text        NOT NULL,
    address         text,
    lat             float8,
    lon             float8,
    phone           text,
    owner_user_id   uuid        -- FK added after users table is created
);

COMMENT ON TABLE restaurants IS 'Restaurant profiles with location and contact info.';


-- =============================================================================
-- 2. USERS
-- Application users. The id references Supabase Auth (auth.users).
-- Role determines permissions: user (search/rate), owner (manage restaurant),
-- admin (full access).
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id              uuid        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email           text        NOT NULL,
    role            text        NOT NULL DEFAULT 'user'
                                CHECK (role IN ('admin', 'owner', 'user')),
    restaurant_id   uuid        REFERENCES restaurants(id) ON DELETE SET NULL
);

COMMENT ON TABLE users IS 'App users linked to Supabase Auth. Role controls access level.';


-- Now add the FK from restaurants.owner_user_id → users.id
ALTER TABLE restaurants
    ADD CONSTRAINT fk_restaurants_owner
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE SET NULL;


-- =============================================================================
-- 3. IMAGES
-- Uploaded images (menu photos, restaurant images, etc.).
-- Created before menus because menus.source_image_id references images.id.
-- =============================================================================
CREATE TABLE IF NOT EXISTS images (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id   uuid        REFERENCES restaurants(id) ON DELETE SET NULL,
    url             text        NOT NULL,
    uploaded_by     uuid        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    upload_ts       timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE images IS 'Uploaded images linked to restaurants and users.';


-- =============================================================================
-- 4. MENUS
-- Daily or weekly menus for a restaurant. May include a source image
-- and raw/parsed text content.
-- =============================================================================
CREATE TABLE IF NOT EXISTS menus (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id   uuid        NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    date            date        NOT NULL,
    source_image_id uuid        REFERENCES images(id) ON DELETE SET NULL,
    raw_text        text,
    parsed_json     jsonb,
    season_tag      text
);

COMMENT ON TABLE menus IS 'Restaurant menus with date, optional image source, and parsed content.';


-- =============================================================================
-- 5. MENU_ITEMS
-- Individual dishes within a menu. May be user-entered or ML-predicted.
-- =============================================================================
CREATE TABLE IF NOT EXISTS menu_items (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    menu_id         uuid        NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
    name            text        NOT NULL,
    description     text,
    price           float8,
    tags            jsonb,
    predicted        boolean     NOT NULL DEFAULT false
);

COMMENT ON TABLE menu_items IS 'Individual dishes in a menu. predicted=true means ML-generated.';


-- =============================================================================
-- 6. RATINGS
-- User ratings and comments on specific menu items.
-- Rating must be between 1 and 5.
-- =============================================================================
CREATE TABLE IF NOT EXISTS ratings (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    menu_item_id    uuid        NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
    rating          int         NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment         text,
    ts              timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE ratings IS 'User ratings (1-5) and comments on menu items.';


-- =============================================================================
-- 7. VISITS
-- Tracks user visits to restaurants and what they ate.
-- =============================================================================
CREATE TABLE IF NOT EXISTS visits (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    restaurant_id   uuid        NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    date            date        NOT NULL,
    ate_items       jsonb
);

COMMENT ON TABLE visits IS 'User visit history to restaurants with items consumed.';


-- =============================================================================
-- 8. PREDICTIONS
-- ML-generated menu predictions for restaurants (future phase).
-- =============================================================================
CREATE TABLE IF NOT EXISTS predictions (
    id                      uuid    PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id           uuid    NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    week_start_date         date    NOT NULL,
    predicted_menu_items    jsonb,
    predicted_services      int,
    model_version           text
);

COMMENT ON TABLE predictions IS 'ML predictions for future menus. To be implemented in a later phase.';
