"use client";

/**
 * frontend/components/auth/SignupForm.tsx
 * Signup form with role selector, conditional restaurant name field,
 * validation, and API error display.
 */

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signup, getUserRole } from "@/lib/api";

export default function SignupForm() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [role, setRole] = useState<"user" | "owner">("user");
    const [restaurantName, setRestaurantName] = useState("");
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
        if (password !== confirmPassword) {
            setError("Las contraseñas no coinciden");
            return;
        }
        if (role === "owner" && !restaurantName.trim()) {
            setError("El nombre del restaurante es obligatorio para dueños");
            return;
        }

        setLoading(true);

        try {
            await signup({
                email,
                password,
                role,
                restaurant_name: role === "owner" ? restaurantName : undefined,
            });

            // Redirect based on role
            const currentRole = getUserRole();
            if (currentRole === "owner") {
                router.push("/restaurant/upload");
            } else {
                router.push("/dashboard");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Error al crear la cuenta");
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="w-full max-w-md space-y-5">
            {/* Role selector */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tipo de cuenta
                </label>
                <div className="grid grid-cols-2 gap-3">
                    <button
                        type="button"
                        onClick={() => setRole("user")}
                        className={`py-2.5 px-4 rounded-lg text-sm font-medium border transition-colors cursor-pointer ${role === "user"
                            ? "bg-amber-600 text-white border-amber-600"
                            : "bg-white text-gray-700 border-gray-300 hover:border-amber-400"
                            }`}
                    >
                        👤 Usuario
                    </button>
                    <button
                        type="button"
                        onClick={() => setRole("owner")}
                        className={`py-2.5 px-4 rounded-lg text-sm font-medium border transition-colors cursor-pointer ${role === "owner"
                            ? "bg-amber-600 text-white border-amber-600"
                            : "bg-white text-gray-700 border-gray-300 hover:border-amber-400"
                            }`}
                    >
                        🍽️ Restaurante
                    </button>
                </div>
            </div>

            <div>
                <label
                    htmlFor="signup-email"
                    className="block text-sm font-medium text-gray-700 mb-1"
                >
                    Email
                </label>
                <input
                    id="signup-email"
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
                    htmlFor="signup-password"
                    className="block text-sm font-medium text-gray-700 mb-1"
                >
                    Contraseña
                </label>
                <input
                    id="signup-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-colors text-black placeholder:text-gray-500"
                    autoComplete="new-password"
                    disabled={loading}
                />
            </div>

            <div>
                <label
                    htmlFor="signup-confirm-password"
                    className="block text-sm font-medium text-gray-700 mb-1"
                >
                    Confirmar contraseña
                </label>
                <input
                    id="signup-confirm-password"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-colors text-black placeholder:text-gray-500"
                    autoComplete="new-password"
                    disabled={loading}
                />
            </div>

            {/* Conditional restaurant name field */}
            {role === "owner" && (
                <div>
                    <label
                        htmlFor="signup-restaurant-name"
                        className="block text-sm font-medium text-gray-700 mb-1"
                    >
                        Nombre del restaurante
                    </label>
                    <input
                        id="signup-restaurant-name"
                        type="text"
                        value={restaurantName}
                        onChange={(e) => setRestaurantName(e.target.value)}
                        placeholder="Mi Restaurante"
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-colors text-black placeholder:text-gray-500"
                        disabled={loading}
                    />
                </div>
            )}

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
                {loading ? "Creando cuenta..." : "Crear cuenta"}
            </button>

            <p className="text-center text-sm text-gray-600">
                ¿Ya tienes cuenta?{" "}
                <Link href="/login" className="text-amber-600 hover:text-amber-700 font-medium">
                    Iniciar sesión
                </Link>
            </p>
        </form>
    );
}
