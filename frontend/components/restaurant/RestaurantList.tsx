"use client";

/**
 * frontend/components/restaurant/RestaurantList.tsx
 * Renders a list of nearby restaurants using RestaurantCard.
 */

import type { NearbyRestaurant } from "@/types";
import RestaurantCard from "./RestaurantCard";

interface RestaurantListProps {
    restaurants: NearbyRestaurant[];
    onViewMenu: (restaurantId: string) => void;
    menuLoadingId?: string | null;
    loading?: boolean;
}

export default function RestaurantList({
    restaurants,
    onViewMenu,
    menuLoadingId = null,
    loading = false,
}: RestaurantListProps) {
    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600" />
                <span className="ml-3 text-gray-500">Buscando restaurantes...</span>
            </div>
        );
    }

    if (restaurants.length === 0) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-500 text-lg">🍽️ No se encontraron restaurantes cercanos</p>
                <p className="text-gray-400 text-sm mt-1">
                    Intenta ampliar el radio de búsqueda o cambiar los filtros
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            <p className="text-sm text-gray-500 mb-2">
                {restaurants.length} restaurante{restaurants.length !== 1 ? "s" : ""} encontrado{restaurants.length !== 1 ? "s" : ""}
            </p>
            {restaurants.map((restaurant) => (
                <RestaurantCard
                    key={restaurant.id}
                    restaurant={restaurant}
                    onViewMenu={onViewMenu}
                    menuLoading={menuLoadingId === restaurant.id}
                />
            ))}
        </div>
    );
}
