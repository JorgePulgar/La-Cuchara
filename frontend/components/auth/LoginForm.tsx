"use client";

/**
 * frontend/components/auth/LoginForm.tsx
 * Login form with email/password fields, validation, and API error display.
 */

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login, getUserRole } from "@/lib/api";

export default function LoginForm() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError("");

        // Client-side validation
        if (!email.trim()) {
            setError("El email es obligatorio");
            return;
        }
        if (!password) {
            setError("La contraseña es obligatoria");
            return;
        }
        if (password.length < 6) {
            setError("La contraseña debe tener al menos 6 caracteres");
            return;
        }

        setLoading(true);

        try {
            await login({ email, password });

            // Redirect based on role
            const role = getUserRole();
            if (role === "owner") {
                router.push("/restaurant/upload");
            } else {
                router.push("/dashboard");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Error al iniciar sesión");
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="w-full max-w-md space-y-5">
            <div>
                <label
                    htmlFor="login-email"
                    className="block text-sm font-medium text-gray-700 mb-1"
                >
                    Email
                </label>
                <input
                    id="login-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="tu@email.com"
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-colors text-black placeholder:text-gray-500"
                    autoComplete="email"
                    disabled={loading}
                />
            </div>

            <div>
                <label
                    htmlFor="login-password"
                    className="block text-sm font-medium text-gray-700 mb-1"
                >
                    Contraseña
                </label>
                <input
                    id="login-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-colors text-black placeholder:text-gray-500"
                    autoComplete="current-password"
                    disabled={loading}
                />
            </div>

            {error && (
                <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg border border-red-200">
                    {error}
                </div>
            )}

            <button
                type="submit"
                disabled={loading}
                className="w-full bg-amber-600 hover:bg-amber-700 disabled:bg-amber-400 text-white font-medium py-2.5 rounded-lg transition-colors cursor-pointer disabled:cursor-not-allowed"
            >
                {loading ? "Iniciando sesión..." : "Iniciar sesión"}
            </button>

            <p className="text-center text-sm text-gray-600">
                ¿No tienes cuenta?{" "}
                <Link href="/signup" className="text-amber-600 hover:text-amber-700 font-medium">
                    Crear cuenta
                </Link>
            </p>
        </form>
    );
}
