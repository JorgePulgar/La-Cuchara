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
        <div className="bg-ecruwhite rounded-2xl border-2 border-thunderbird-200 p-6 shadow-md hover:shadow-xl transition-all border-b-4 border-b-thunderbird-100">
            <div className="flex justify-between items-start mb-3">
                <div>
                    <h3 className="text-xl font-bold text-thunderbird-950">
                        {restaurant.name}
                    </h3>
                    {restaurant.address && (
                        <p className="text-xs font-medium text-gray-500 mt-1">
                            📍 {restaurant.address}
                        </p>
                    )}
                </div>
                <div className="text-right flex-shrink-0 ml-4">
                    <span className="inline-block bg-thunderbird-700 text-ecruwhite text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-lg shadow-sm">
                        {restaurant.distance_km.toFixed(1)} KM
                    </span>
                </div>
            </div>

            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    {restaurant.average_rating != null && (
                        <div className="flex items-center gap-1">
                            <span className="text-thunderbird-600">★</span>
                            <span className="text-sm font-bold text-thunderbird-900">
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
                    className="px-5 py-2.5 bg-ecruwhite text-thunderbird-700 border-2 border-thunderbird-700 hover:bg-white disabled:opacity-50 text-[10px] font-black uppercase tracking-widest rounded-xl shadow-sm transition-all cursor-pointer disabled:cursor-not-allowed"
                >
                    {menuLoading ? "..." : "Ver menú"}
                </button>
            </div>
        </div>
    );
}
