"use client";

/**
 * frontend/app/dashboard/page.tsx
 * User dashboard with location-based restaurant discovery.
 * Shows LocationInput → then filters, search, and restaurant list.
 */

import Navbar from "@/components/layout/Navbar";
import ProtectedRoute from "@/components/layout/ProtectedRoute";
import LocationInput from "@/components/location/LocationInput";
import FiltersPanel from "@/components/restaurant/FiltersPanel";
import RestaurantList from "@/components/restaurant/RestaurantList";
import MenuItemSearch from "@/components/restaurant/MenuItemSearch";
import { useEffect, useState, useCallback } from "react";
import { getMe, getNearbyRestaurants, getTodayMenu } from "@/lib/api";
import type { NearbyRestaurant, MenuWithItems } from "@/types";

export default function DashboardPage() {
    const [userEmail, setUserEmail] = useState("");

    // Location state
    const [location, setLocation] = useState<{ lat: number; lon: number } | null>(null);

    // Restaurants state
    const [restaurants, setRestaurants] = useState<NearbyRestaurant[]>([]);
    const [loadingRestaurants, setLoadingRestaurants] = useState(false);

    // Filters state
    const [radiusKm, setRadiusKm] = useState(5);
    const [minRating, setMinRating] = useState<number | null>(null);
    const [hasMenuToday, setHasMenuToday] = useState(false);

    // Menu modal state
    const [menuLoadingId, setMenuLoadingId] = useState<string | null>(null);
    const [selectedMenu, setSelectedMenu] = useState<MenuWithItems | null>(null);
    const [selectedRestaurantName, setSelectedRestaurantName] = useState("");
    const [menuError, setMenuError] = useState("");

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

    // Fetch restaurants when location or filters change
    const fetchRestaurants = useCallback(async () => {
        if (!location) return;

        setLoadingRestaurants(true);
        try {
            const data = await getNearbyRestaurants(location.lat, location.lon, {
                radius_km: radiusKm,
                min_rating: minRating ?? undefined,
                has_menu_today: hasMenuToday,
            });
            setRestaurants(data);
        } catch {
            setRestaurants([]);
        } finally {
            setLoadingRestaurants(false);
        }
    }, [location, radiusKm, minRating, hasMenuToday]);

    useEffect(() => {
        fetchRestaurants();
    }, [fetchRestaurants]);

    const handleLocationSet = (lat: number, lon: number) => {
        setLocation({ lat, lon });
    };

    const handleViewMenu = async (restaurantId: string) => {
        setMenuLoadingId(restaurantId);
        setMenuError("");
        setSelectedMenu(null);

        const restaurant = restaurants.find((r) => r.id === restaurantId);
        setSelectedRestaurantName(restaurant?.name ?? "Restaurante");

        try {
            const menu = await getTodayMenu(restaurantId);
            setSelectedMenu(menu);
        } catch (err) {
            setMenuError(
                err instanceof Error ? err.message : "Error al cargar el menú"
            );
        } finally {
            setMenuLoadingId(null);
        }
    };

    return (
        <ProtectedRoute requiredRole="user">
            <Navbar />
            <main className="min-h-screen bg-gray-50 px-4 py-8">
                <div className="max-w-5xl mx-auto">
                    {/* Header */}
                    <div className="mb-8">
                        <h1 className="text-2xl font-bold text-gray-900">
                            ¡Bienvenido a La Cuchara!
                        </h1>
                        {userEmail && (
                            <p className="text-gray-500 mt-1">
                                Conectado como <span className="font-medium">{userEmail}</span>
                            </p>
                        )}
                    </div>

                    {/* Location input (shown if location not set) */}
                    {!location ? (
                        <LocationInput onLocationSet={handleLocationSet} />
                    ) : (
                        <>
                            {/* Location badge + change button */}
                            <div className="flex items-center gap-2 mb-6">
                                <span className="bg-green-100 text-green-800 text-sm px-3 py-1 rounded-full">
                                    📍 Ubicación establecida ({location.lat.toFixed(4)}, {location.lon.toFixed(4)})
                                </span>
                                <button
                                    onClick={() => {
                                        setLocation(null);
                                        setRestaurants([]);
                                        setSelectedMenu(null);
                                    }}
                                    className="text-sm text-gray-500 hover:text-gray-700 underline cursor-pointer"
                                >
                                    Cambiar
                                </button>
                            </div>

                            {/* Search bar */}
                            <MenuItemSearch
                                lat={location.lat}
                                lon={location.lon}
                                radiusKm={radiusKm}
                            />

                            {/* Filters + Restaurant list */}
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                                {/* Filters sidebar */}
                                <div className="md:col-span-1">
                                    <FiltersPanel
                                        radiusKm={radiusKm}
                                        onRadiusChange={setRadiusKm}
                                        minRating={minRating}
                                        onMinRatingChange={setMinRating}
                                        hasMenuToday={hasMenuToday}
                                        onHasMenuTodayChange={setHasMenuToday}
                                    />
                                </div>

                                {/* Restaurant list */}
                                <div className="md:col-span-3">
                                    <RestaurantList
                                        restaurants={restaurants}
                                        onViewMenu={handleViewMenu}
                                        menuLoadingId={menuLoadingId}
                                        loading={loadingRestaurants}
                                    />
                                </div>
                            </div>

                            {/* Today's menu modal / panel */}
                            {(selectedMenu || menuError) && (
                                <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
                                    <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[80vh] overflow-y-auto p-6">
                                        <div className="flex justify-between items-start mb-4">
                                            <h3 className="text-lg font-bold text-gray-900">
                                                📋 Menú de hoy — {selectedRestaurantName}
                                            </h3>
                                            <button
                                                onClick={() => {
                                                    setSelectedMenu(null);
                                                    setMenuError("");
                                                }}
                                                className="text-gray-400 hover:text-gray-600 text-xl cursor-pointer"
                                            >
                                                ✕
                                            </button>
                                        </div>

                                        {menuError ? (
                                            <div className="bg-amber-50 text-amber-800 text-sm px-4 py-3 rounded-lg border border-amber-200">
                                                {menuError}
                                            </div>
                                        ) : selectedMenu ? (
                                            <>
                                                {selectedMenu.season_tag && (
                                                    <span className="inline-block bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded-full mb-3">
                                                        {selectedMenu.season_tag}
                                                    </span>
                                                )}

                                                {selectedMenu.items.length === 0 ? (
                                                    <p className="text-gray-500 text-sm italic">
                                                        No hay platos registrados para hoy.
                                                    </p>
                                                ) : (
                                                    <div className="space-y-6">
                                                        {/* Section grouping: Primeros, Segundos, Otros */}
                                                        {[
                                                            { label: "Primeros", filter: "primero" },
                                                            { label: "Segundos", filter: "segundo" },
                                                            { label: "Otros", filter: null }
                                                        ].map((section) => {
                                                            const items = selectedMenu.items.filter(item => {
                                                                const course = item.tags ? (item.tags as any).course : null;
                                                                if (section.filter === null) {
                                                                    return course !== "primero" && course !== 'segundo';
                                                                }
                                                                return course === section.filter;
                                                            });

                                                            if (items.length === 0) return null;

                                                            return (
                                                                <div key={section.label}>
                                                                    <h4 className="text-xs font-bold text-amber-600 uppercase tracking-widest mb-3 border-b border-amber-50 pb-1">
                                                                        {section.label}
                                                                    </h4>
                                                                    <ul className="divide-y divide-gray-50">
                                                                        {items.map((item) => (
                                                                            <li key={item.id} className="py-2.5">
                                                                                <div className="flex justify-between items-start">
                                                                                    <div>
                                                                                        <p className="font-semibold text-black">
                                                                                            {item.name}
                                                                                        </p>
                                                                                        {item.description && (
                                                                                            <p className="text-sm text-gray-800 mt-1 leading-relaxed">
                                                                                                {item.description}
                                                                                            </p>
                                                                                        )}
                                                                                    </div>
                                                                                    {item.price != null && (
                                                                                        <span className="font-bold text-gray-900 ml-3 bg-gray-50 px-2 py-1 rounded text-sm">
                                                                                            {item.price.toFixed(2)} €
                                                                                        </span>
                                                                                    )}
                                                                                </div>
                                                                            </li>
                                                                        ))}
                                                                    </ul>
                                                                </div>
                                                            );
                                                        })}

                                                        {/* Inclusion Badges */}
                                                        <div className="flex flex-wrap gap-2 pt-4 border-t border-gray-100">
                                                            {!!selectedMenu.parsed_json?.MenuBreadIncluded && (
                                                                <span className="bg-orange-50 text-orange-700 px-2.5 py-1 rounded-full text-xs font-bold border border-orange-100">
                                                                    🍞 Pan incluido
                                                                </span>
                                                            )}
                                                            {!!selectedMenu.parsed_json?.MenuDessertIncluded && (
                                                                <span className="bg-pink-50 text-pink-700 px-2.5 py-1 rounded-full text-xs font-bold border border-pink-100">
                                                                    🍮 Postre incluido
                                                                </span>
                                                            )}
                                                            {!!selectedMenu.parsed_json?.MenuDrinkIncluded && (
                                                                <span className="bg-blue-50 text-blue-700 px-2.5 py-1 rounded-full text-xs font-bold border border-blue-100">
                                                                    🥤 Bebida incluida
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>
                                                )}
                                            </>
                                        ) : null}
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </main>
        </ProtectedRoute>
    );
}
