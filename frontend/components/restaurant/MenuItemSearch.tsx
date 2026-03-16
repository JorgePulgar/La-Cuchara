"use client";

/**
 * frontend/components/restaurant/MenuItemSearch.tsx
 * Search bar for menu items with debounced search and results display.
 */

import { useState, useEffect, useCallback } from "react";
import { searchMenuItems } from "@/lib/api";
import type { MenuItemSearchResult } from "@/types";

interface MenuItemSearchProps {
    lat: number;
    lon: number;
    radiusKm: number;
}

export default function MenuItemSearch({ lat, lon, radiusKm }: MenuItemSearchProps) {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<MenuItemSearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);

    const doSearch = useCallback(
        async (q: string) => {
            if (!q.trim()) {
                setResults([]);
                setSearched(false);
                return;
            }

            setLoading(true);
            try {
                const data = await searchMenuItems(q, lat, lon, radiusKm);
                setResults(data);
                setSearched(true);
            } catch {
                setResults([]);
                setSearched(true);
            } finally {
                setLoading(false);
            }
        },
        [lat, lon, radiusKm]
    );

    // Debounce the search by 400ms
    useEffect(() => {
        const timer = setTimeout(() => {
            doSearch(query);
        }, 400);

        return () => clearTimeout(timer);
    }, [query, doSearch]);

    return (
        <div className="mb-6">
            <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                    🔍
                </span>
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Buscar platos (ej: paella, ensalada, tortilla...)"
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-colors text-black placeholder:text-gray-500 bg-white"
                />
                {loading && (
                    <span className="absolute right-3 top-1/2 -translate-y-1/2">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-amber-600" />
                    </span>
                )}
            </div>

            {/* Results */}
            {searched && query.trim() && (
                <div className="mt-3 bg-white rounded-xl border border-gray-200 overflow-hidden">
                    {results.length === 0 ? (
                        <div className="px-4 py-6 text-center text-gray-500 text-sm">
                            No se encontraron platos para &quot;{query}&quot;
                        </div>
                    ) : (
                        <ul className="divide-y divide-gray-100">
                            {results.map((item) => (
                                <li key={item.id} className="px-4 py-3 hover:bg-gray-50">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <p className="font-medium text-gray-900">
                                                {item.name}
                                            </p>
                                            {item.description && (
                                                <p className="text-sm text-gray-500 mt-0.5">
                                                    {item.description}
                                                </p>
                                            )}
                                            <p className="text-xs text-amber-700 mt-1">
                                                🍽️ {item.restaurant_name}
                                            </p>
                                        </div>
                                        {item.price != null && (
                                            <span className="text-sm font-semibold text-gray-800 ml-3 flex-shrink-0">
                                                {item.price.toFixed(2)} €
                                            </span>
                                        )}
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            )}
        </div>
    );
}
