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
        <nav className="w-full bg-thunderbird-700 text-ecruwhite px-6 py-4 flex items-center justify-between shadow-md border-b border-thunderbird-800">
            <Link href="/" className="text-3xl font-brand tracking-wide hover:opacity-90 transition-opacity">
                La Cuchara
            </Link>

            <div className="flex items-center gap-4">
                {authenticated ? (
                    <>
                        {role === "user" && (
                            <Link
                                href="/dashboard"
                                className="text-sm border-b border-transparent hover:border-ecruwhite transition-all font-medium"
                            >
                                Dashboard
                            </Link>
                        )}
                        {role === "owner" && (
                            <Link
                                href="/restaurant/dashboard"
                                className="text-sm border-b border-transparent hover:border-ecruwhite transition-all font-medium"
                            >
                                Mi Restaurante
                            </Link>
                        )}
                        <button
                            onClick={handleLogout}
                            className="text-sm bg-ecruwhite text-thunderbird-700 hover:bg-ecruwhite/80 px-4 py-2 rounded-lg font-bold shadow-sm transition-all cursor-pointer"
                        >
                            Cerrar sesión
                        </button>
                    </>
                ) : (
                    <>
                        <Link
                            href="/login"
                            className="text-sm border-b border-transparent hover:border-ecruwhite transition-all font-medium"
                        >
                            Iniciar sesión
                        </Link>
                        <Link
                            href="/signup"
                            className="text-sm bg-ecruwhite text-thunderbird-700 hover:bg-ecruwhite/80 px-4 py-2 rounded-lg font-bold shadow-sm transition-all"
                        >
                            Crear cuenta
                        </Link>
                    </>
                )}
            </div>
        </nav>
    );
}
