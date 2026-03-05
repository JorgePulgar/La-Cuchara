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

/**
 * Helper to make API requests with proper headers and error handling.
 */
async function apiFetch<T>(
    path: string,
    options: RequestInit = {}
): Promise<T> {
    const url = `${API_BASE}${path}`;

    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string>),
    };

    // Add auth token if available
    const token =
        typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (!response.ok) {
            const error: ApiError = await response.json().catch(() => ({
                detail: `HTTP ${response.status}: ${response.statusText}`,
            }));
            throw new Error(error.detail);
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

    // Store token in localStorage
    if (typeof window !== "undefined") {
        localStorage.setItem("access_token", result.access_token);
        localStorage.setItem("user_role", result.role);
    }

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

    // Store token in localStorage
    if (typeof window !== "undefined") {
        localStorage.setItem("access_token", result.access_token);
        localStorage.setItem("user_role", result.role);
    }

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
        if (typeof window !== "undefined") {
            localStorage.removeItem("access_token");
            localStorage.removeItem("user_role");
        }
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
