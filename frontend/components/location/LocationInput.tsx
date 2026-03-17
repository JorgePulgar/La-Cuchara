"use client";

import { useState } from "react";

/**
 * frontend/components/location/LocationInput.tsx
 * Lets the user set their location via browser geolocation or manual address input.
 * Uses the new Thunderbird and Ecruwhite palette.
 */

interface LocationInputProps {
    onLocationSet: (lat: number, lon: number) => void;
}

export default function LocationInput({ onLocationSet }: LocationInputProps) {
    const [address, setAddress] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleUseMyLocation = () => {
        setError("");
        setLoading(true);

        if (!navigator.geolocation) {
            setError("Tu navegador no soporta geolocalización");
            setLoading(false);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                onLocationSet(position.coords.latitude, position.coords.longitude);
                setLoading(false);
            },
            (err) => {
                switch (err.code) {
                    case err.PERMISSION_DENIED:
                        setError("Permiso de ubicación denegado. Por favor, habilítalo en la configuración de tu navegador.");
                        break;
                    case err.POSITION_UNAVAILABLE:
                        setError("Información de ubicación no disponible.");
                        break;
                    case err.TIMEOUT:
                        setError("La solicitud de ubicación ha expirado.");
                        break;
                    default:
                        setError("Error desconocido al obtener la ubicación.");
                }
                setLoading(false);
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    };

    const handleManualAddress = async () => {
        if (!address.trim()) {
            setError("Introduce una dirección");
            return;
        }

        setError("");
        setLoading(true);

        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=json&limit=1`,
                { headers: { "User-Agent": "LaCuchara/0.1 (development)" } }
            );
            const results = await response.json();

            if (!results || results.length === 0) {
                setError("No se encontró la dirección. Intenta con una dirección más específica.");
                setLoading(false);
                return;
            }

            const lat = parseFloat(results[0].lat);
            const lon = parseFloat(results[0].lon);
            onLocationSet(lat, lon);
        } catch {
            setError("Error al buscar la dirección. Inténtalo de nuevo.");
        } finally {
            setLoading(false);
        }
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
                    onClick={handleUseMyLocation}
                    disabled={loading}
                    className="w-full bg-thunderbird-700 hover:bg-thunderbird-800 disabled:opacity-50 text-ecruwhite font-black uppercase tracking-widest py-4 rounded-xl shadow-lg transition-all transform hover:scale-[1.02] active:scale-95 cursor-pointer flex items-center justify-center gap-2"
                >
                    📍 {loading ? "Obteniendo ubicación..." : "Usar mi ubicación actual"}
                </button>

                <div className="relative flex items-center gap-4 py-2">
                    <div className="flex-1 h-px bg-gray-200"></div>
                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">O ingresa tu dirección</span>
                    <div className="flex-1 h-px bg-gray-200"></div>
                </div>

                <div className="flex gap-2">
                    <input
                        type="text"
                        value={address}
                        onChange={(e) => setAddress(e.target.value)}
                        placeholder="Ej: Calle Gran Vía, Madrid"
                        className="flex-1 w-full px-4 py-3 bg-ecruwhite/50 border-2 border-ecruwhite rounded-xl focus:ring-2 focus:ring-thunderbird-700 focus:border-thunderbird-700 outline-none transition-all text-black placeholder:text-gray-300 font-medium"
                        disabled={loading}
                        onKeyDown={(e) => e.key === "Enter" && handleManualAddress()}
                    />
                    <button
                        onClick={handleManualAddress}
                        disabled={loading || !address.trim()}
                        className="bg-ecruwhite text-thunderbird-700 border-2 border-thunderbird-700 hover:bg-white disabled:opacity-50 font-black uppercase tracking-widest text-sm px-6 py-3 rounded-xl shadow-sm transition-all cursor-pointer"
                    >
                        Buscar
                    </button>
                </div>
            </div>
        </div>
    );
}
