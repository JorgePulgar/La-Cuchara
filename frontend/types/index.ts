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

export interface NearbyRestaurant {
    id: string;
    name: string;
    address?: string | null;
    lat?: number | null;
    lon?: number | null;
    phone?: string | null;
    owner_user_id?: string | null;
    distance_km: number;
    average_rating?: number | null;
}

export interface MenuWithItems {
    id: string;
    restaurant_id: string;
    date: string;
    source_image_id?: string | null;
    raw_text?: string | null;
    parsed_json?: Record<string, unknown> | null;
    season_tag?: string | null;
    items: MenuItem[];
}

export interface MenuItemSearchResult {
    id: string;
    menu_id: string;
    name: string;
    description?: string | null;
    price?: number | null;
    tags?: string[] | null;
    predicted: boolean;
    restaurant_id: string;
    restaurant_name: string;
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

// =============================================================================
// Predictions
// =============================================================================

export interface PredictedMenuItem {
    normalized_name: string;
    score: number;
    rank: number;
    avg_units_sold?: number;
    avg_units_sold_hist?: number;
    avg_rating?: number;
    avg_rating_hist?: number;
    times_used?: number;
    times_used_hist?: number;
}

export interface PredictedDay {
    date?: string;
    weekday: string;
    season_tag?: string;
    primeros: PredictedMenuItem[];
    segundos: PredictedMenuItem[];
}

export interface PredictedMenuPayload {
    restaurant_id: string;
    season_tag?: string;
    model_version?: string;
    days: PredictedDay[];
}

export interface Prediction {
    id?: string | null;
    restaurant_id: string;
    week_start_date: string;
    predicted_menu_items: PredictedMenuPayload | Record<string, unknown>;
    predicted_services?: number | null;
    model_version?: string | null;
}
