"use client";

/**
 * frontend/components/restaurant/RestaurantCard.tsx
 * Displays a single restaurant with its name, address, distance, rating,
 * and a button to view today's menu.
 */

import type { NearbyRestaurant } from "@/types";

interface RestaurantCardProps {
    restaurant: NearbyRestaurant;
    onViewMenu: (restaurantId: string) => void;
    menuLoading?: boolean;
    hasMenuToday?: boolean;
}

export default function RestaurantCard({
    restaurant,
    onViewMenu,
    menuLoading = false,
}: RestaurantCardProps) {
    return (
        <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-3">
                <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                        {restaurant.name}
                    </h3>
                    {restaurant.address && (
                        <p className="text-sm text-gray-500 mt-0.5">
                            📍 {restaurant.address}
                        </p>
                    )}
                </div>
                <div className="text-right flex-shrink-0 ml-4">
                    <span className="inline-block bg-amber-100 text-amber-800 text-sm font-medium px-2.5 py-1 rounded-full">
                        {restaurant.distance_km.toFixed(1)} km
                    </span>
                </div>
            </div>

            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    {restaurant.average_rating != null && (
                        <div className="flex items-center gap-1">
                            <span className="text-amber-500">⭐</span>
                            <span className="text-sm font-medium text-gray-700">
                                {restaurant.average_rating.toFixed(1)}
                            </span>
                        </div>
                    )}
                    {restaurant.phone && (
                        <span className="text-sm text-gray-500">
                            📞 {restaurant.phone}
                        </span>
                    )}
                </div>

                <button
                    onClick={() => onViewMenu(restaurant.id)}
                    disabled={menuLoading}
                    className="px-4 py-2 bg-amber-600 hover:bg-amber-700 disabled:bg-amber-400 text-white text-sm font-medium rounded-lg transition-colors cursor-pointer disabled:cursor-not-allowed"
                >
                    {menuLoading ? "Cargando..." : "Ver menú de hoy"}
                </button>
            </div>
        </div>
    );
}
