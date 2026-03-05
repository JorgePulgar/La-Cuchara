"use client";

/**
 * frontend/components/layout/ProtectedRoute.tsx
 * HOC that checks for a valid token and required role.
 * Redirects to /login if unauthenticated or unauthorized.
 */

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { isAuthenticated, getUserRole } from "@/lib/api";

interface ProtectedRouteProps {
    children: React.ReactNode;
    requiredRole?: "user" | "owner" | "admin";
}

export default function ProtectedRoute({
    children,
    requiredRole,
}: ProtectedRouteProps) {
    const router = useRouter();
    const [authorized, setAuthorized] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const checkAuth = () => {
            if (!isAuthenticated()) {
                router.push("/login");
                return;
            }

            if (requiredRole) {
                const currentRole = getUserRole();
                if (currentRole !== requiredRole && currentRole !== "admin") {
                    // Admin can access everything, otherwise must match role
                    router.push("/login");
                    return;
                }
            }

            setAuthorized(true);
            setLoading(false);
        };

        checkAuth();
    }, [router, requiredRole]);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
            </div>
        );
    }

    if (!authorized) {
        return null;
    }

    return <>{children}</>;
}
