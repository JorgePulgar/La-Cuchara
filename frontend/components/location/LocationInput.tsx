"use client";

import { useState } from "react";

/**
 * frontend/components/location/LocationInput.tsx
 * Allows the user to set their location (lat/lon) to discover nearby restaurants.
 * Uses the new Thunderbird and Ecruwhite palette.
 */

interface LocationInputProps {
    onLocationSet: (lat: number, lon: number) => void;
}

export default function LocationInput({ onLocationSet }: LocationInputProps) {
    const [lat, setLat] = useState("");
    const [lon, setLon] = useState("");
    const [error, setError] = useState("");

    const handleUseCurrentLocation = () => {
        if (!navigator.geolocation) {
            setError("Tu navegador no soporta geolocalización");
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                onLocationSet(position.coords.latitude, position.coords.longitude);
            },
            () => {
                setError("No se pudo obtener tu ubicación. Por favor, introdúcela manualmente.");
            }
        );
    };

    const handleManualSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const l = parseFloat(lat);
        const lo = parseFloat(lon);

        if (isNaN(l) || isNaN(lo)) {
            setError("Por favor, introduce coordenadas válidas");
            return;
        }

        onLocationSet(l, lo);
    };

    return (
        <div className="bg-ecruwhite rounded-3xl border-4 border-thunderbird-100 shadow-2xl p-8 max-w-xl mx-auto">
            <div className="text-center mb-8">
                <h2 className="text-3xl font-brand text-thunderbird-700 mb-2">
                    Encuentra comida cerca de ti
                </h2>
                <p className="text-sm font-medium text-gray-500">
                    Establece tu ubicación para descubrir los mejores menús del día.
                </p>
            </div>

            {error && (
                <div className="bg-thunderbird-50 text-thunderbird-800 text-sm px-4 py-3 rounded-xl border border-thunderbird-200 mb-6">
                    ⚠️ {error}
                </div>
            )}

            <div className="space-y-6">
                <button
                    onClick={handleUseCurrentLocation}
                    className="w-full bg-thunderbird-700 hover:bg-thunderbird-800 text-ecruwhite font-black uppercase tracking-widest py-4 rounded-xl shadow-lg transition-all transform hover:scale-[1.02] active:scale-95 cursor-pointer flex items-center justify-center gap-2"
                >
                    📍 Usar mi ubicación actual
                </button>

                <div className="relative flex items-center gap-4 py-2">
                    <div className="flex-1 h-px bg-gray-200"></div>
                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">O manual</span>
                    <div className="flex-1 h-px bg-gray-200"></div>
                </div>

                <form onSubmit={handleManualSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-[10px] font-black text-thunderbird-700 uppercase tracking-widest mb-1 mx-1">Latitud</label>
                        <input
                            type="number"
                            step="any"
                            value={lat}
                            onChange={(e) => setLat(e.target.value)}
                            placeholder="Ej: 40.4167"
                            className="w-full px-4 py-3 bg-ecruwhite/50 border-2 border-ecruwhite rounded-xl focus:ring-2 focus:ring-thunderbird-700 focus:border-thunderbird-700 outline-none transition-all text-black placeholder:text-gray-300 font-medium"
                        />
                    </div>
                    <div>
                        <label className="block text-[10px] font-black text-thunderbird-700 uppercase tracking-widest mb-1 mx-1">Longitud</label>
                        <input
                            type="number"
                            step="any"
                            value={lon}
                            onChange={(e) => setLon(e.target.value)}
                            placeholder="Ej: -3.7037"
                            className="w-full px-4 py-3 bg-ecruwhite/50 border-2 border-ecruwhite rounded-xl focus:ring-2 focus:ring-thunderbird-700 focus:border-thunderbird-700 outline-none transition-all text-black placeholder:text-gray-300 font-medium"
                        />
                    </div>
                    <button
                        type="submit"
                        className="md:col-span-2 mt-2 bg-ecruwhite text-thunderbird-700 border-2 border-thunderbird-700 hover:bg-white font-black uppercase tracking-widest text-sm py-3 rounded-xl shadow-sm transition-all cursor-pointer"
                    >
                        Establecer manual
                    </button>
                </form>
            </div>
        </div>
    );
}
