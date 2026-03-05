"use client";

/**
 * frontend/components/restaurant/MenuUpload.tsx
 * Menu upload form: date, image file, season tag.
 * Shows loading state and success/error feedback.
 */

import { useState, type FormEvent, type ChangeEvent } from "react";

export default function MenuUpload() {
    const [menuDate, setMenuDate] = useState("");
    const [imageFile, setImageFile] = useState<File | null>(null);
    const [seasonTag, setSeasonTag] = useState("");
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState("");

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setImageFile(e.target.files[0]);
        }
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError("");
        setSuccess(false);

        if (!menuDate) {
            setError("La fecha del menú es obligatoria");
            return;
        }

        setLoading(true);

        try {
            // TODO: conectar Supabase
            // Placeholder: POST /menus/upload endpoint doesn't exist yet.
            // Simulating a successful upload.
            await new Promise((resolve) => setTimeout(resolve, 1000));

            setSuccess(true);
            setMenuDate("");
            setImageFile(null);
            setSeasonTag("");

            // Reset file input
            const fileInput = document.getElementById(
                "upload-image"
            ) as HTMLInputElement;
            if (fileInput) fileInput.value = "";
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Error al subir el menú"
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="w-full max-w-lg space-y-5">
            <div>
                <label
                    htmlFor="upload-date"
                    className="block text-sm font-medium text-gray-700 mb-1"
                >
                    Fecha del menú
                </label>
                <input
                    id="upload-date"
                    type="date"
                    value={menuDate}
                    onChange={(e) => setMenuDate(e.target.value)}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-colors text-black"
                    disabled={loading}
                />
            </div>

            <div>
                <label
                    htmlFor="upload-image"
                    className="block text-sm font-medium text-gray-700 mb-1"
                >
                    Imagen del menú
                </label>
                <input
                    id="upload-image"
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-amber-50 file:text-amber-700 hover:file:bg-amber-100 transition-colors"
                    disabled={loading}
                />
                {imageFile && (
                    <p className="text-xs text-gray-500 mt-1">
                        Archivo: {imageFile.name}
                    </p>
                )}
            </div>

            <div>
                <label
                    htmlFor="upload-season"
                    className="block text-sm font-medium text-gray-700 mb-1"
                >
                    Etiqueta de temporada{" "}
                    <span className="text-gray-400">(opcional)</span>
                </label>
                <input
                    id="upload-season"
                    type="text"
                    value={seasonTag}
                    onChange={(e) => setSeasonTag(e.target.value)}
                    placeholder="Ej: verano, navidad, primavera..."
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-colors text-black placeholder:text-gray-500"
                    disabled={loading}
                />
            </div>

            {error && (
                <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg border border-red-200">
                    {error}
                </div>
            )}

            {success && (
                <div className="bg-green-50 text-green-700 text-sm px-4 py-3 rounded-lg border border-green-200">
                    ✅ Menú subido con éxito (simulado — endpoint pendiente de
                    implementación)
                </div>
            )}

            <button
                type="submit"
                disabled={loading}
                className="w-full bg-amber-600 hover:bg-amber-700 disabled:bg-amber-400 text-white font-medium py-2.5 rounded-lg transition-colors cursor-pointer disabled:cursor-not-allowed"
            >
                {loading ? "Subiendo menú..." : "Subir menú"}
            </button>
        </form>
    );
}
