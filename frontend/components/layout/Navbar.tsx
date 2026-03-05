"use client";

/**
 * frontend/components/layout/Navbar.tsx
 * Navigation bar with app name, navigation links, and logout button.
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { logout, isAuthenticated, getUserRole } from "@/lib/api";

export default function Navbar() {
    const router = useRouter();
    const [authenticated, setAuthenticated] = useState(false);
    const [role, setRole] = useState<string | null>(null);

    useEffect(() => {
        setAuthenticated(isAuthenticated());
        setRole(getUserRole());
    }, []);

    const handleLogout = async () => {
        await logout();
        setAuthenticated(false);
        setRole(null);
        router.push("/login");
    };

    return (
        <nav className="w-full bg-gray-900 text-white px-6 py-4 flex items-center justify-between shadow-md">
            <Link href="/" className="text-xl font-bold tracking-tight hover:opacity-80 transition-opacity">
                🍽️ La Cuchara
            </Link>

            <div className="flex items-center gap-4">
                {authenticated ? (
                    <>
                        {role === "user" && (
                            <Link
                                href="/dashboard"
                                className="text-sm hover:text-amber-400 transition-colors"
                            >
                                Dashboard
                            </Link>
                        )}
                        {role === "owner" && (
                            <Link
                                href="/restaurant/upload"
                                className="text-sm hover:text-amber-400 transition-colors"
                            >
                                Subir menú
                            </Link>
                        )}
                        <button
                            onClick={handleLogout}
                            className="text-sm bg-red-600 hover:bg-red-700 px-3 py-1.5 rounded-md transition-colors cursor-pointer"
                        >
                            Cerrar sesión
                        </button>
                    </>
                ) : (
                    <>
                        <Link
                            href="/login"
                            className="text-sm hover:text-amber-400 transition-colors"
                        >
                            Iniciar sesión
                        </Link>
                        <Link
                            href="/signup"
                            className="text-sm bg-amber-600 hover:bg-amber-700 px-3 py-1.5 rounded-md transition-colors"
                        >
                            Crear cuenta
                        </Link>
                    </>
                )}
            </div>
        </nav>
    );
}
