/**
 * frontend/lib/api.ts
 * Typed functions to call the FastAPI backend.
 * Uses NEXT_PUBLIC_API_URL as base URL.
 */

// TODO: conectar Supabase

import type {
    LoginRequest,
    SignupRequest,
    TokenResponse,
    User,
    ApiError,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type RefreshResponse = TokenResponse;

function getStoredAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
}

function getStoredRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("refresh_token");
}

function persistSession(session: TokenResponse): void {
    if (typeof window === "undefined") return;
    localStorage.setItem("access_token", session.access_token);
    localStorage.setItem("refresh_token", session.refresh_token);
    localStorage.setItem("user_role", session.role);
}

function clearStoredSession(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user_role");
}

async function refreshAccessToken(): Promise<string | null> {
    const refreshToken = getStoredRefreshToken();
    if (!refreshToken) return null;

    const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
        clearStoredSession();
        return null;
    }

    const refreshed = (await response.json()) as RefreshResponse;
    persistSession(refreshed);
    return refreshed.access_token;
}

/**
 * Helper to make API requests with proper headers and error handling.
 */
async function apiFetch<T>(
    path: string,
    options: RequestInit = {},
    retryOnUnauthorized = true,
): Promise<T> {
    const url = `${API_BASE}${path}`;

    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string>),
    };

    // Add auth token if available
    const token = getStoredAccessToken();
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (response.status === 401 && retryOnUnauthorized) {
            const refreshedToken = await refreshAccessToken();
            if (refreshedToken) {
                return apiFetch<T>(path, options, false);
            }
        }

        if (!response.ok) {
            const errorBody = await response.json().catch(() => ({
                detail: `HTTP ${response.status}: ${response.statusText}`,
            }));
            // FastAPI returns detail as a string OR an array of validation errors
            let message: string;
            if (typeof errorBody.detail === "string") {
                message = errorBody.detail;
            } else if (Array.isArray(errorBody.detail)) {
                message = errorBody.detail
                    .map((err: { msg?: string; loc?: string[] }) =>
                        err.msg ?? JSON.stringify(err)
                    )
                    .join(", ");
            } else {
                message = `HTTP ${response.status}: ${response.statusText}`;
            }
            throw new Error(message);
        }

        return (await response.json()) as T;
    } catch (error) {
        if (error instanceof Error) {
            throw error;
        }
        throw new Error("An unexpected error occurred");
    }
}

// =============================================================================
// Auth API functions
// =============================================================================

/**
 * POST /auth/login
 */
export async function login(data: LoginRequest): Promise<TokenResponse> {
    const result = await apiFetch<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
    });

    persistSession(result);

    return result;
}

/**
 * POST /auth/signup
 */
export async function signup(data: SignupRequest): Promise<TokenResponse> {
    const result = await apiFetch<TokenResponse>("/auth/signup", {
        method: "POST",
        body: JSON.stringify(data),
    });

    persistSession(result);

    return result;
}

/**
 * POST /auth/logout
 */
export async function logout(): Promise<void> {
    try {
        await apiFetch("/auth/logout", { method: "POST" });
    } catch {
        // Still clear local storage even if API call fails
    } finally {
        clearStoredSession();
    }
}

/**
 * GET /auth/me
 */
export async function getMe(): Promise<User> {
    return apiFetch<User>("/auth/me");
}

// =============================================================================
// Token helpers
// =============================================================================

/**
 * Check if there's a stored access token.
 */
export function isAuthenticated(): boolean {
    if (typeof window === "undefined") return false;
    return !!localStorage.getItem("access_token");
}

/**
 * Get the stored user role.
 */
export function getUserRole(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("user_role");
}

// =============================================================================
// Image Analysis API Functions (Azure Content Understanding)
// =============================================================================

export interface BoundingRegion {
    page_number: number | null;
    polygon: Record<string, unknown>[] | null;
}

export interface ExtractedField {
    name: string;
    content: string;
    confidence: number;
    bounding_regions: BoundingRegion[];
}

export interface ImageAnalysisResponse {
    status: string;
    fields: Record<string, unknown>;
    items: ExtractedField[];
}

export interface SaveMenuRequest {
    date: string;
    season_tag?: string | null;
    fields: Record<string, unknown>;
    items: string[];
}

export interface SavedMenuItem {
    id: string;
    menu_id: string;
    name: string;
    description?: string | null;
    price?: number | null;
    tags?: string[] | null;
    predicted: boolean;
}

export interface SavedMenu {
    id: string;
    restaurant_id: string;
    date: string;
    source_image_id?: string | null;
    raw_text?: string | null;
    parsed_json?: Record<string, unknown> | null;
    season_tag?: string | null;
}

export interface SaveMenuResponse {
    menu: SavedMenu;
    menu_items: SavedMenuItem[];
}

/**
 * POST /images/analyze-menu
 * Analyzes a menu image using Azure Content Understanding.
 *
 * The image is sent as binary data to the backend, which:
 * 1. Encodes it to base64
 * 2. Sends it to Azure Content Understanding API
 * 3. Polls the operation until completion
 * 4. Returns extracted fields and structured items
 *
 * @param imageFile - The menu image file to analyze
 * @param restaurantId - Optional restaurant ID to associate with the analysis
 * @returns ImageAnalysisResponse with extracted fields and structured items
 * @throws Error if the image format is invalid, file is too large, or analysis fails
 */
export async function analyzeMenuImage(
    imageFile: File,
    restaurantId?: string
): Promise<ImageAnalysisResponse> {
    const formData = new FormData();
    formData.append("file", imageFile);

    if (restaurantId) {
        formData.append("restaurant_id", restaurantId);
    }

    const url = `${API_BASE}/images/analyze-menu`;

    const headers: Record<string, string> = {};

    // Add auth token if available
    const token = getStoredAccessToken();
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, {
            method: "POST",
            headers,
            body: formData,
        });

        if (response.status === 401) {
            const refreshedToken = await refreshAccessToken();
            if (refreshedToken) {
                return analyzeMenuImage(imageFile, restaurantId);
            }
        }

        if (!response.ok) {
            const errorBody = await response.json().catch(() => ({
                detail: `HTTP ${response.status}: ${response.statusText}`,
            }));

            let message: string;
            if (typeof errorBody.detail === "string") {
                message = errorBody.detail;
            } else if (Array.isArray(errorBody.detail)) {
                message = errorBody.detail
                    .map((err: { msg?: string; loc?: string[] }) =>
                        err.msg ?? JSON.stringify(err)
                    )
                    .join(", ");
            } else {
                message = `HTTP ${response.status}: ${response.statusText}`;
            }
            throw new Error(message);
        }

        return (await response.json()) as ImageAnalysisResponse;
    } catch (error) {
        if (error instanceof Error) {
            throw error;
        }
        throw new Error("An unexpected error occurred during image analysis");
    }
}

/**
 * POST /menus
 * Persists the corrected menu and its menu items in the backend database.
 */
export async function saveMenu(data: SaveMenuRequest): Promise<SaveMenuResponse> {
    return apiFetch<SaveMenuResponse>("/menus", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

// =============================================================================
// Restaurant Discovery API Functions
// =============================================================================

import type {
    NearbyRestaurant,
    MenuWithItems,
    MenuItemSearchResult,
} from "@/types";

export interface NearbyFilters {
    radius_km?: number;
    min_rating?: number;
    has_menu_today?: boolean;
}

/**
 * GET /restaurants/nearby
 */
export async function getNearbyRestaurants(
    lat: number,
    lon: number,
    filters?: NearbyFilters,
): Promise<NearbyRestaurant[]> {
    const params = new URLSearchParams({
        lat: lat.toString(),
        lon: lon.toString(),
    });
    if (filters?.radius_km) params.set("radius_km", filters.radius_km.toString());
    if (filters?.min_rating) params.set("min_rating", filters.min_rating.toString());
    if (filters?.has_menu_today) params.set("has_menu_today", "true");

    return apiFetch<NearbyRestaurant[]>(`/restaurants/nearby?${params.toString()}`);
}

/**
 * GET /restaurants/{restaurantId}/menu/today
 */
export async function getTodayMenu(restaurantId: string): Promise<MenuWithItems> {
    return apiFetch<MenuWithItems>(`/restaurants/${restaurantId}/menu/today`);
}

/**
 * GET /menus/search
 */
export async function searchMenuItems(
    q: string,
    lat: number,
    lon: number,
    radiusKm: number = 5,
): Promise<MenuItemSearchResult[]> {
    const params = new URLSearchParams({
        q,
        lat: lat.toString(),
        lon: lon.toString(),
        radius_km: radiusKm.toString(),
    });
    return apiFetch<MenuItemSearchResult[]>(`/menus/search?${params.toString()}`);
}
/**
 * GET /menus/owner
 */
export async function getOwnerMenus(): Promise<SaveMenuResponse[]> {
    return apiFetch<SaveMenuResponse[]>("/menus/owner");
}

/**
 * POST /menus/owner/{menu_id}/reuse
 */
export async function reuseMenu(menuId: string): Promise<SaveMenuResponse> {
    return apiFetch<SaveMenuResponse>(`/menus/owner/${menuId}/reuse`, {
        method: "POST",
    });
}
