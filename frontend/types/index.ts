/**
 * frontend/types/index.ts
 * TypeScript types matching the Pydantic schemas in backend/app/models/schemas.py.
 */

// =============================================================================
// Auth
// =============================================================================

export interface LoginRequest {
    email: string;
    password: string;
}

export interface SignupRequest {
    email: string;
    password: string;
    role: "user" | "owner";
    restaurant_name?: string;
    restaurant_address?: string;
    restaurant_phone?: string;
}

export interface TokenResponse {
    access_token: string;
    refresh_token: string;
    user_id: string;
    email: string;
    role: "admin" | "owner" | "user";
}

// =============================================================================
// Users
// =============================================================================

export interface User {
    id: string;
    email: string;
    role: "admin" | "owner" | "user";
    restaurant_id?: string | null;
}

// =============================================================================
// Restaurants
// =============================================================================

export interface Restaurant {
    id: string;
    name: string;
    address?: string | null;
    lat?: number | null;
    lon?: number | null;
    phone?: string | null;
    owner_user_id?: string | null;
}

// =============================================================================
// Menus
// =============================================================================

export interface Menu {
    id: string;
    restaurant_id: string;
    date: string;
    source_image_id?: string | null;
    raw_text?: string | null;
    parsed_json?: Record<string, unknown> | null;
    season_tag?: string | null;
}

// =============================================================================
// Menu Items
// =============================================================================

export interface MenuItem {
    id: string;
    menu_id: string;
    name: string;
    description?: string | null;
    price?: number | null;
    tags?: string[] | null;
    predicted: boolean;
}

// =============================================================================
// Images
// =============================================================================

export interface Image {
    id: string;
    restaurant_id?: string | null;
    url: string;
    uploaded_by: string;
    upload_ts: string;
}

// =============================================================================
// Ratings
// =============================================================================

export interface RatingCreate {
    menu_item_id: string;
    rating: number;
    comment?: string;
}

export interface Rating {
    id: string;
    user_id: string;
    menu_item_id: string;
    rating: number;
    comment?: string | null;
    ts: string;
}

// =============================================================================
// API Error
// =============================================================================

export interface ApiError {
    detail: string;
}
