"use client";

// User dashboard — Task 6.1
// Protected (role: user). Uses ProtectedRoute.

import Navbar from "@/components/layout/Navbar";
import ProtectedRoute from "@/components/layout/ProtectedRoute";
import { useEffect, useState } from "react";
import { getMe } from "@/lib/api";

export default function DashboardPage() {
    const [userEmail, setUserEmail] = useState("");

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const user = await getMe();
                setUserEmail(user.email);
            } catch {
                // Will be handled by ProtectedRoute if unauthenticated
            }
        };
        fetchUser();
    }, []);

    return (
        <ProtectedRoute requiredRole="user">
            <Navbar />
            <main className="min-h-screen bg-gray-50 px-4 py-12">
                <div className="max-w-3xl mx-auto">
                    <div className="bg-white rounded-2xl shadow-lg p-8">
                        <h1 className="text-2xl font-bold text-gray-900 mb-2">
                            ¡Bienvenido a La Cuchara!
                        </h1>
                        {userEmail && (
                            <p className="text-gray-600 mb-6">
                                Conectado como <span className="font-medium">{userEmail}</span>
                            </p>
                        )}

                        <div className="border-t border-gray-200 pt-6">
                            <h2 className="text-lg font-semibold text-gray-800 mb-3">
                                🔍 Buscar restaurantes
                            </h2>
                            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-amber-800 text-sm">
                                <p className="font-medium">Próximamente</p>
                                <p className="mt-1 text-amber-700">
                                    La búsqueda de restaurantes y filtros por tipo de comida
                                    estarán disponibles en una próxima actualización.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </ProtectedRoute>
    );
}
