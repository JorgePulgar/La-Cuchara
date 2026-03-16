"use client";

/**
 * frontend/components/restaurant/FiltersPanel.tsx
 * Filter controls for restaurant discovery: distance, min rating, menu today toggle.
 */

interface FiltersPanelProps {
    radiusKm: number;
    onRadiusChange: (value: number) => void;
    minRating: number | null;
    onMinRatingChange: (value: number | null) => void;
    hasMenuToday: boolean;
    onHasMenuTodayChange: (value: boolean) => void;
}

export default function FiltersPanel({
    radiusKm,
    onRadiusChange,
    minRating,
    onMinRatingChange,
    hasMenuToday,
    onHasMenuTodayChange,
}: FiltersPanelProps) {
    return (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-800 mb-4 uppercase tracking-wide">
                Filtros
            </h3>

            {/* Distance slider */}
            <div className="mb-5">
                <label className="flex justify-between text-sm text-gray-700 mb-1.5">
                    <span>Distancia máxima</span>
                    <span className="font-medium text-amber-700">{radiusKm} km</span>
                </label>
                <input
                    type="range"
                    min={1}
                    max={20}
                    step={1}
                    value={radiusKm}
                    onChange={(e) => onRadiusChange(Number(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-amber-600"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                    <span>1 km</span>
                    <span>20 km</span>
                </div>
            </div>

            {/* Min rating */}
            <div className="mb-5">
                <label className="block text-sm text-gray-700 mb-1.5">
                    Valoración mínima
                </label>
                <div className="flex gap-1.5">
                    {[1, 2, 3, 4, 5].map((star) => (
                        <button
                            key={star}
                            onClick={() => onMinRatingChange(minRating === star ? null : star)}
                            className={`w-9 h-9 rounded-lg flex items-center justify-center text-sm font-medium transition-colors cursor-pointer ${minRating !== null && star <= minRating
                                    ? "bg-amber-500 text-white"
                                    : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                                }`}
                        >
                            {star}⭐
                        </button>
                    ))}
                </div>
            </div>

            {/* Has menu today toggle */}
            <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700">Solo con menú hoy</span>
                <button
                    onClick={() => onHasMenuTodayChange(!hasMenuToday)}
                    className={`relative w-11 h-6 rounded-full transition-colors cursor-pointer ${hasMenuToday ? "bg-amber-600" : "bg-gray-300"
                        }`}
                >
                    <span
                        className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${hasMenuToday ? "translate-x-5" : ""
                            }`}
                    />
                </button>
            </div>
        </div>
    );
}
