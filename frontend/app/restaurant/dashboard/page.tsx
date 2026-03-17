"use client";

import Navbar from "@/components/layout/Navbar";
import ProtectedRoute from "@/components/layout/ProtectedRoute";
import { useEffect, useState } from "react";
import { getOwnerMenus, type SaveMenuResponse } from "@/lib/api";
import Link from "next/link";

export default function OwnerDashboard() {
    const [menus, setMenus] = useState<SaveMenuResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchMenus = async () => {
            try {
                const data = await getOwnerMenus();
                // Filter out empty menus (no items)
                const filtered = data.filter(m => m.menu_items.length > 0);
                setMenus(filtered);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Error al cargar los menús");
            } finally {
                setLoading(false);
            }
        };
        fetchMenus();
    }, []);

    return (
        <ProtectedRoute requiredRole="owner">
            <Navbar />
            <main className="min-h-screen bg-gray-50 px-4 py-12">
                <div className="max-w-4xl mx-auto">
                    <div className="flex justify-between items-center mb-8">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">Panel del Restaurante</h1>
                            <p className="text-gray-600 mt-1">Gestiona tus menús y platos</p>
                        </div>
                        <Link
                            href="/restaurant/upload"
                            className="bg-amber-600 hover:bg-amber-700 text-white font-bold py-2.5 px-6 rounded-xl shadow-lg transition-all transform hover:scale-105"
                        >
                            + Subir nuevo menú
                        </Link>
                    </div>

                    {loading ? (
                        <div className="flex justify-center py-20">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600"></div>
                        </div>
                    ) : error ? (
                        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl">
                            {error}
                        </div>
                    ) : menus.length === 0 ? (
                        <div className="bg-white rounded-2xl shadow-sm p-12 text-center border border-gray-100">
                            <div className="text-5xl mb-4">📋</div>
                            <h2 className="text-xl font-semibold text-gray-900 mb-2">Aún no tienes menús guardados</h2>
                            <p className="text-gray-500 mb-8 max-w-sm mx-auto">
                                Sube tu primer menú para empezar a aparecer en las búsquedas de los clientes.
                            </p>
                            <Link
                                href="/restaurant/upload"
                                className="text-amber-600 font-bold hover:underline"
                            >
                                Subir mi primer menú &rarr;
                            </Link>
                        </div>
                    ) : (
                        <div className="grid gap-6">
                            {menus.map((m) => (
                                <div key={m.menu.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
                                    <div className="bg-gray-50/50 px-6 py-4 flex justify-between items-center border-b border-gray-100">
                                        <div className="flex items-center gap-4">
                                            <span className="text-lg font-bold text-gray-900">
                                                {new Date(m.menu.date).toLocaleDateString("es-ES", {
                                                    weekday: 'long',
                                                    day: 'numeric',
                                                    month: 'long'
                                                })}
                                            </span>
                                            {m.menu.season_tag && (
                                                <span className="bg-amber-100 text-amber-800 text-[10px] uppercase tracking-wider font-black px-2 py-0.5 rounded">
                                                    {m.menu.season_tag}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <div className="p-6">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-4">
                                            {/* Primeros */}
                                            <div>
                                                <h3 className="text-[10px] font-black text-amber-600 uppercase tracking-widest mb-3">Primeros platos</h3>
                                                <ul className="space-y-2">
                                                    {m.menu_items
                                                        .filter(item => {
                                                            // Parse item name if it's a JSON string (Point 6 fix)
                                                            let course = "primero";
                                                            try {
                                                                if (item.name.startsWith('{')) {
                                                                    const parsed = JSON.parse(item.name);
                                                                    course = parsed.course;
                                                                }
                                                            } catch { }
                                                            return course === "primero";
                                                        })
                                                        .map(item => {
                                                            let displayName = item.name;
                                                            try {
                                                                if (item.name.startsWith('{')) {
                                                                    const parsed = JSON.parse(item.name);
                                                                    displayName = parsed.name;
                                                                }
                                                            } catch { }
                                                            return (
                                                                <li key={item.id} className="text-sm text-black font-medium border-l-2 border-gray-100 pl-3">
                                                                    {displayName}
                                                                </li>
                                                            );
                                                        })}
                                                </ul>
                                            </div>
                                            {/* Segundos */}
                                            <div>
                                                <h3 className="text-[10px] font-black text-amber-600 uppercase tracking-widest mb-3">Segundos platos</h3>
                                                <ul className="space-y-2">
                                                    {m.menu_items
                                                        .filter(item => {
                                                            let course = "segundo";
                                                            try {
                                                                if (item.name.startsWith('{')) {
                                                                    const parsed = JSON.parse(item.name);
                                                                    course = parsed.course;
                                                                }
                                                            } catch { }
                                                            return course === "segundo";
                                                        })
                                                        .map(item => {
                                                            let displayName = item.name;
                                                            try {
                                                                if (item.name.startsWith('{')) {
                                                                    const parsed = JSON.parse(item.name);
                                                                    displayName = parsed.name;
                                                                }
                                                            } catch { }
                                                            return (
                                                                <li key={item.id} className="text-sm text-black font-medium border-l-2 border-gray-100 pl-3">
                                                                    {displayName}
                                                                </li>
                                                            );
                                                        })}
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </main>
        </ProtectedRoute>
    );
}
