"use client";

/**
 * frontend/components/location/LocationInput.tsx
 * Lets the user set their location via browser geolocation or manual address input.
 */

import { useState } from "react";

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
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-lg mx-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-2 text-center">
                📍 ¿Dónde estás?
            </h2>
            <p className="text-gray-500 text-sm mb-6 text-center">
                Necesitamos tu ubicación para encontrar restaurantes cercanos
            </p>

            {/* Option 1: Browser geolocation */}
            <button
                onClick={handleUseMyLocation}
                disabled={loading}
                className="w-full bg-amber-600 hover:bg-amber-700 disabled:bg-amber-400 text-white font-medium py-3 rounded-lg transition-colors cursor-pointer disabled:cursor-not-allowed mb-4"
            >
                {loading ? "Obteniendo ubicación..." : "📍 Usar mi ubicación"}
            </button>

            <div className="flex items-center gap-3 my-4">
                <div className="flex-1 border-t border-gray-200" />
                <span className="text-gray-400 text-sm">o</span>
                <div className="flex-1 border-t border-gray-200" />
            </div>

            {/* Option 2: Manual address */}
            <div className="flex gap-2">
                <input
                    type="text"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    placeholder="Escribe una dirección..."
                    className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-colors text-black placeholder:text-gray-500"
                    disabled={loading}
                    onKeyDown={(e) => e.key === "Enter" && handleManualAddress()}
                />
                <button
                    onClick={handleManualAddress}
                    disabled={loading || !address.trim()}
                    className="px-5 py-2.5 bg-gray-800 hover:bg-gray-900 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors cursor-pointer disabled:cursor-not-allowed"
                >
                    Buscar
                </button>
            </div>

            {error && (
                <div className="mt-4 bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg border border-red-200">
                    {error}
                </div>
            )}
        </div>
    );
}
