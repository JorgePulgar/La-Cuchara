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
            <main className="min-h-screen px-4 py-8">
                <div className="max-w-5xl mx-auto">
                    {/* Header */}
                    <div className="mb-8">
                        <h1 className="text-3xl font-brand text-thunderbird-700">
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
                                <span className="bg-thunderbird-100 text-thunderbird-800 text-sm font-bold px-3 py-1 rounded-full shadow-sm border border-thunderbird-200">
                                    📍 Ubicación established ({location.lat.toFixed(4)}, {location.lon.toFixed(4)})
                                </span>
                                <button
                                    onClick={() => {
                                        setLocation(null);
                                        setRestaurants([]);
                                        setSelectedMenu(null);
                                    }}
                                    className="text-sm text-thunderbird-700 hover:text-thunderbird-900 font-bold underline cursor-pointer"
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
                                    <div className="app-card bg-ecruwhite rounded-3xl shadow-2xl border-4 border-thunderbird-100 max-w-lg w-full max-h-[80vh] overflow-y-auto p-8">
                                        <div className="flex justify-between items-start mb-6">
                                            <h3 className="text-2xl font-brand text-thunderbird-700">
                                                Menú de hoy — {selectedRestaurantName}
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
                                            <div className="bg-thunderbird-50 text-thunderbird-800 text-sm px-4 py-3 rounded-lg border border-thunderbird-200">
                                                {menuError}
                                            </div>
                                        ) : selectedMenu ? (
                                            <>
                                                {selectedMenu.season_tag && (
                                                    <span className="inline-block bg-thunderbird-700 text-ecruwhite text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-md mb-4">
                                                        {selectedMenu.season_tag}
                                                    </span>
                                                )}

                                                {selectedMenu.items.length === 0 ? (
                                                    <p className="text-gray-500 text-sm italic">
                                                        No hay platos registrados para hoy.
                                                    </p>
                                                ) : (
                                                    <div className="space-y-6">
                                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-4">
                                                            {/* Primeros */}
                                                            <div>
                                                                <h4 className="text-[10px] font-black text-thunderbird-600 uppercase tracking-widest mb-3">Primeros platos</h4>
                                                                <ul className="space-y-4">
                                                                    {selectedMenu.items
                                                                        .filter(item => {
                                                                            let course = "primero";
                                                                            try {
                                                                                if (item.name.startsWith('{')) {
                                                                                    const parsed = JSON.parse(item.name);
                                                                                    course = parsed.course;
                                                                                } else if (item.tags && (item.tags as any).course) {
                                                                                    course = (item.tags as any).course;
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
                                                                                <li key={item.id} className="border-l-2 border-gray-100 pl-3">
                                                                                    <p className="text-sm font-semibold text-black">
                                                                                        {String(displayName)}
                                                                                    </p>
                                                                                    {item.description && (
                                                                                        <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                                                                                            {item.description}
                                                                                        </p>
                                                                                    )}
                                                                                </li>
                                                                            );
                                                                        })}
                                                                </ul>
                                                            </div>
                                                            {/* Segundos */}
                                                            <div>
                                                                <h4 className="text-[10px] font-black text-thunderbird-600 uppercase tracking-widest mb-3">Segundos platos</h4>
                                                                <ul className="space-y-4">
                                                                    {selectedMenu.items
                                                                        .filter(item => {
                                                                            let course = "segundo";
                                                                            try {
                                                                                if (item.name.startsWith('{')) {
                                                                                    const parsed = JSON.parse(item.name);
                                                                                    course = parsed.course;
                                                                                } else if (item.tags && (item.tags as any).course) {
                                                                                    course = (item.tags as any).course;
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
                                                                                <li key={item.id} className="border-l-2 border-gray-100 pl-3">
                                                                                    <p className="text-sm font-semibold text-black">
                                                                                        {String(displayName)}
                                                                                    </p>
                                                                                    {item.description && (
                                                                                        <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                                                                                            {item.description}
                                                                                        </p>
                                                                                    )}
                                                                                </li>
                                                                            );
                                                                        })}
                                                                </ul>
                                                            </div>
                                                        </div>

                                                        {/* Inclusion Badges */}
                                                        <div className="flex flex-wrap gap-2 pt-4 border-t border-gray-100">
                                                            {Boolean(selectedMenu.parsed_json?.MenuBreadIncluded) && (
                                                                <span className="bg-orange-100 text-orange-800 text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full shadow-sm">
                                                                    🍞 Pan
                                                                </span>
                                                            )}
                                                            {Boolean(selectedMenu.parsed_json?.MenuDrinkIncluded) && (
                                                                <span className="bg-blue-100 text-blue-800 text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full shadow-sm">
                                                                    🥤 Bebida
                                                                </span>
                                                            )}
                                                            {Boolean(selectedMenu.parsed_json?.MenuDessertIncluded) && (
                                                                <span className="bg-pink-100 text-pink-800 text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full shadow-sm">
                                                                    🍮 Postre
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
