"use client";

import Navbar from "@/components/layout/Navbar";
import ProtectedRoute from "@/components/layout/ProtectedRoute";
import { useEffect, useMemo, useState } from "react";
import {
    generateOwnerPrediction,
    getOwnerMenus,
    getOwnerPrediction,
    reuseMenu,
    type SaveMenuResponse,
} from "@/lib/api";
import Link from "next/link";
import type { PredictedDay, PredictedMenuItem, Prediction } from "@/types";

function getNextMondayISO(): string {
    const today = new Date();
    const day = today.getDay();
    const daysUntilMonday = (8 - day) % 7 || 7;
    const nextMonday = new Date(today);
    nextMonday.setDate(today.getDate() + daysUntilMonday);
    const yyyy = nextMonday.getFullYear();
    const mm = String(nextMonday.getMonth() + 1).padStart(2, "0");
    const dd = String(nextMonday.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
}

function parseIsoDateInput(value: string): Date | null {
    const [year, month, day] = value.split("-").map(Number);
    if (!year || !month || !day) return null;

    const parsed = new Date(year, month - 1, day);
    if (Number.isNaN(parsed.getTime())) return null;

    return parsed;
}

function isMondayDate(value: string): boolean {
    const parsed = parseIsoDateInput(value);
    if (!parsed) return false;
    return parsed.getDay() === 1;
}

function getWeekdayLabel(weekday: string): string {
    const labels: Record<string, string> = {
        monday: "Lunes",
        tuesday: "Martes",
        wednesday: "Miércoles",
        thursday: "Jueves",
        friday: "Viernes",
        saturday: "Sábado",
        sunday: "Domingo",
    };

    return labels[weekday.toLowerCase()] ?? weekday;
}

function getMetricValue(item: PredictedMenuItem, key: "sold" | "rating" | "times"): number {
    if (key === "sold") {
        return item.avg_units_sold ?? item.avg_units_sold_hist ?? 0;
    }
    if (key === "rating") {
        return item.avg_rating ?? item.avg_rating_hist ?? 0;
    }

    return item.times_used ?? item.times_used_hist ?? 0;
}

function extractPredictionDays(prediction: Prediction | null): PredictedDay[] {
    if (!prediction) return [];

    const payload = prediction.predicted_menu_items;
    if (!payload || typeof payload !== "object") return [];

    const maybeDays = (payload as { days?: unknown }).days;
    if (!Array.isArray(maybeDays)) return [];

    return maybeDays as PredictedDay[];
}

function extractPredictionMeta(prediction: Prediction | null): {
    modelVersion: string;
    seasonTag: string;
} {
    if (!prediction) {
        return {
            modelVersion: "-",
            seasonTag: "-",
        };
    }

    const payload = prediction.predicted_menu_items;
    const payloadObj = payload && typeof payload === "object" ? payload as Record<string, unknown> : {};

    const modelVersionFromPayload = typeof payloadObj.model_version === "string" ? payloadObj.model_version : null;
    const seasonTagFromPayload = typeof payloadObj.season_tag === "string" ? payloadObj.season_tag : null;

    return {
        modelVersion: prediction.model_version ?? modelVersionFromPayload ?? "-",
        seasonTag: seasonTagFromPayload ?? "-",
    };
}

export default function OwnerDashboard() {
    const [menus, setMenus] = useState<SaveMenuResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [showAll, setShowAll] = useState(false);
    const [savingId, setSavingId] = useState<string | null>(null);

    const [predictionWeekStart, setPredictionWeekStart] = useState(getNextMondayISO);
    const [prediction, setPrediction] = useState<Prediction | null>(null);
    const [predictionError, setPredictionError] = useState("");
    const [queryingPrediction, setQueryingPrediction] = useState(false);
    const [generatingPrediction, setGeneratingPrediction] = useState(false);

    const fetchMenus = async () => {
        try {
            setLoading(true);
            const data = await getOwnerMenus();
            // Filter out empty menus (no items)
            const filtered = data.filter(m => m.menu_items.length > 0);
            setMenus(filtered);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Error al cargar los menús");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMenus();
    }, []);

    const handleReuse = async (menuData: SaveMenuResponse) => {
        try {
            setSavingId(menuData.menu.id);
            setError("");

            await reuseMenu(menuData.menu.id);

            // Refresh to show the updated list
            await fetchMenus();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Error al reutilizar el menú");
        } finally {
            setSavingId(null);
        }
    };

    const now = new Date();
    const todayStr = new Date(now.getTime() - (now.getTimezoneOffset() * 60000)).toISOString().slice(0, 10);
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();

    const displayedMenus = showAll
        ? menus
        : menus.filter(m => {
            const menuDate = new Date(m.menu.date);
            return menuDate.getMonth() === currentMonth && menuDate.getFullYear() === currentYear;
        });

    const selectedDateIsMonday = isMondayDate(predictionWeekStart);
    const predictionDays = useMemo(() => extractPredictionDays(prediction), [prediction]);
    const predictionMeta = useMemo(() => extractPredictionMeta(prediction), [prediction]);

    const handleQueryPrediction = async () => {
        if (!selectedDateIsMonday) {
            setPredictionError("La fecha seleccionada debe ser lunes para consultar la predicción semanal.");
            return;
        }

        try {
            setPredictionError("");
            setQueryingPrediction(true);
            const result = await getOwnerPrediction(predictionWeekStart);
            setPrediction(result);
        } catch (err) {
            setPrediction(null);
            setPredictionError(err instanceof Error ? err.message : "No se pudo consultar la predicción");
        } finally {
            setQueryingPrediction(false);
        }
    };

    const handleGeneratePrediction = async () => {
        if (!selectedDateIsMonday) {
            setPredictionError("La fecha seleccionada debe ser lunes para generar la predicción semanal.");
            return;
        }

        try {
            setPredictionError("");
            setGeneratingPrediction(true);
            const result = await generateOwnerPrediction(predictionWeekStart);
            setPrediction(result);
        } catch (err) {
            setPredictionError(err instanceof Error ? err.message : "No se pudo generar la predicción");
        } finally {
            setGeneratingPrediction(false);
        }
    };

    return (
        <ProtectedRoute requiredRole="owner">
            <Navbar />
            <main className="min-h-screen px-4 py-12">
                <div className="max-w-4xl mx-auto">
                    <div className="flex justify-between items-center mb-8">
                        <div>
                            <h1 className="text-3xl font-brand text-thunderbird-700">Panel del Restaurante</h1>
                            <p className="text-sm font-medium text-gray-700 mt-1">Gestiona tus menús y platos</p>
                        </div>
                        <Link
                            href="/restaurant/upload"
                            className="bg-thunderbird-700 hover:bg-thunderbird-800 text-ecruwhite font-bold py-3 px-8 rounded-xl shadow-lg transition-all transform hover:scale-105"
                        >
                            + Subir nuevo menú
                        </Link>
                    </div>

                    <div className="flex justify-end mb-4">
                        <button
                            onClick={() => setShowAll(!showAll)}
                            className="text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors border border-gray-300 rounded-lg px-4 py-2 bg-ecruwhite cursor-pointer hover:bg-white flex items-center gap-2 shadow-sm"
                        >
                            {showAll ? "Ocultar meses anteriores" : "Mostrar todos los menús"}
                        </button>
                    </div>

                    <section className="app-card mb-8 bg-ecruwhite rounded-2xl shadow-[0_12px_28px_rgba(15,23,42,0.10)] p-6">
                        <div className="flex flex-col gap-5">
                            <div>
                                <h2 className="text-xl font-bold text-thunderbird-900">Predicción menú semana siguiente</h2>
                                <p className="text-sm text-gray-700 mt-1">
                                    Consulta una predicción existente o genera una nueva para la semana que empieza en lunes.
                                </p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-[220px_1fr] gap-4 items-end">
                                <div>
                                    <label htmlFor="prediction-week-start" className="block text-sm font-semibold text-gray-800 mb-2">
                                        Inicio de semana
                                    </label>
                                    <input
                                        id="prediction-week-start"
                                        type="date"
                                        value={predictionWeekStart}
                                        onChange={(e) => setPredictionWeekStart(e.target.value)}
                                        className="w-full rounded-lg border border-thunderbird-200 bg-ecruwhite px-3 py-2 text-sm text-gray-950 shadow-sm focus:outline-none focus:ring-2 focus:ring-thunderbird-400"
                                    />
                                </div>

                                <div className="flex flex-wrap items-center gap-3">
                                    <button
                                        onClick={handleQueryPrediction}
                                        disabled={queryingPrediction || generatingPrediction}
                                        className="bg-ecruwhite border border-thunderbird-200 text-gray-900 font-semibold px-4 py-2 rounded-lg hover:bg-thunderbird-50 transition-colors cursor-pointer shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
                                    >
                                        {queryingPrediction ? "Consultando..." : "Consultar predicción"}
                                    </button>
                                    <button
                                        onClick={handleGeneratePrediction}
                                        disabled={queryingPrediction || generatingPrediction}
                                        className="bg-thunderbird-700 text-ecruwhite font-semibold px-4 py-2 rounded-lg hover:bg-thunderbird-800 transition-colors cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
                                    >
                                        {generatingPrediction ? "Generando..." : "Generar predicción"}
                                    </button>
                                    <button
                                        onClick={() => setPredictionWeekStart(getNextMondayISO())}
                                        disabled={queryingPrediction || generatingPrediction}
                                        className="text-sm text-gray-800 hover:text-gray-950 underline cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
                                    >
                                        Usar próximo lunes
                                    </button>
                                </div>
                            </div>

                            {!selectedDateIsMonday && (
                                <div className="bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-3 rounded-lg">
                                    Selecciona un lunes para consultar o generar la predicción.
                                </div>
                            )}

                            {predictionError && (
                                <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
                                    {predictionError}
                                </div>
                            )}

                            {prediction && (
                                <div className="rounded-xl overflow-hidden bg-thunderbird-50/40 shadow-[0_8px_22px_rgba(15,23,42,0.08)]">
                                    <div className="bg-ecruwhite px-4 py-3 flex flex-wrap items-center gap-3 shadow-sm">
                                        <span className="text-xs font-black uppercase tracking-widest text-thunderbird-800">
                                            Semana {prediction.week_start_date}
                                        </span>
                                        <span className="text-xs bg-thunderbird-50 px-2 py-1 rounded-md text-gray-800 font-semibold shadow-sm">
                                            Modelo: {predictionMeta.modelVersion}
                                        </span>
                                        <span className="text-xs bg-thunderbird-50 px-2 py-1 rounded-md text-gray-800 font-semibold shadow-sm">
                                            Temporada: {predictionMeta.seasonTag}
                                        </span>
                                    </div>

                                    {predictionDays.length === 0 ? (
                                        <div className="p-4 text-sm text-gray-700">
                                            La predicción no incluye días en el formato esperado.
                                        </div>
                                    ) : (
                                        <div className="grid gap-4 p-4">
                                            {predictionDays.map((day, index) => (
                                                <div key={`${day.weekday}-${day.date ?? index}`} className="rounded-xl p-4 bg-ecruwhite shadow-[0_6px_18px_rgba(15,23,42,0.08)]">
                                                    <h3 className="text-sm font-bold text-thunderbird-900 mb-3">
                                                        {getWeekdayLabel(day.weekday)}
                                                        {day.date ? ` - ${day.date}` : ""}
                                                    </h3>

                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                        <div>
                                                            <p className="text-[10px] font-black uppercase tracking-widest text-thunderbird-700 mb-2">Primeros</p>
                                                            {day.primeros.length === 0 ? (
                                                                <p className="text-xs text-gray-600 italic">Sin propuestas</p>
                                                            ) : (
                                                                <ul className="space-y-2">
                                                                    {day.primeros.map((item) => (
                                                                        <li key={`first-${day.weekday}-${item.rank}-${item.normalized_name}`} className="bg-thunderbird-50/45 rounded-lg px-3 py-2 shadow-sm">
                                                                            <p className="text-sm font-semibold text-gray-900">
                                                                                {item.rank}. {item.normalized_name}
                                                                            </p>
                                                                            <p className="text-xs text-gray-600">
                                                                                score {item.score.toFixed(3)} • ventas {getMetricValue(item, "sold").toFixed(2)} • rating {getMetricValue(item, "rating").toFixed(2)} • usos {getMetricValue(item, "times")}
                                                                            </p>
                                                                        </li>
                                                                    ))}
                                                                </ul>
                                                            )}
                                                        </div>

                                                        <div>
                                                            <p className="text-[10px] font-black uppercase tracking-widest text-thunderbird-700 mb-2">Segundos</p>
                                                            {day.segundos.length === 0 ? (
                                                                <p className="text-xs text-gray-600 italic">Sin propuestas</p>
                                                            ) : (
                                                                <ul className="space-y-2">
                                                                    {day.segundos.map((item) => (
                                                                        <li key={`second-${day.weekday}-${item.rank}-${item.normalized_name}`} className="bg-thunderbird-50/45 rounded-lg px-3 py-2 shadow-sm">
                                                                            <p className="text-sm font-semibold text-gray-900">
                                                                                {item.rank}. {item.normalized_name}
                                                                            </p>
                                                                            <p className="text-xs text-gray-600">
                                                                                score {item.score.toFixed(3)} • ventas {getMetricValue(item, "sold").toFixed(2)} • rating {getMetricValue(item, "rating").toFixed(2)} • usos {getMetricValue(item, "times")}
                                                                            </p>
                                                                        </li>
                                                                    ))}
                                                                </ul>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </section>

                    {loading ? (
                        <div className="flex justify-center py-20">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-thunderbird-700"></div>
                        </div>
                    ) : error ? (
                        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl">
                            {error}
                        </div>
                    ) : menus.length === 0 ? (
                        <div className="app-card bg-ecruwhite rounded-2xl shadow-[0_14px_30px_rgba(15,23,42,0.10)] p-12 text-center">
                            <div className="text-5xl mb-4">📋</div>
                            <h2 className="text-xl font-semibold text-gray-900 mb-2">Aún no tienes menús guardados</h2>
                            <p className="text-gray-700 mb-8 max-w-sm mx-auto">
                                Sube tu primer menú para empezar a aparecer en las búsquedas de los clientes.
                            </p>
                            <Link
                                href="/restaurant/upload"
                                className="text-thunderbird-600 font-bold hover:underline"
                            >
                                Subir mi primer menú &rarr;
                            </Link>
                        </div>
                    ) : (
                        <div className="grid gap-6">
                            {displayedMenus.map((m) => (
                                <div key={m.menu.id} className="app-card bg-ecruwhite rounded-2xl shadow-[0_12px_24px_rgba(15,23,42,0.10)] overflow-hidden hover:shadow-[0_16px_32px_rgba(15,23,42,0.14)] transition-shadow">
                                    <div className="bg-thunderbird-50/35 px-6 py-4 flex justify-between items-center shadow-sm">
                                        <div className="flex items-center gap-4">
                                            <span className="text-lg font-bold text-thunderbird-900">
                                                {new Date(m.menu.date).toLocaleDateString("es-ES", {
                                                    weekday: 'long',
                                                    day: 'numeric',
                                                    month: 'long'
                                                })}
                                            </span>
                                            {m.menu.date === todayStr && (
                                                <span className="bg-green-100 text-green-800 text-[10px] uppercase tracking-wider font-black px-2 py-0.5 rounded">
                                                    ✨ Menú de Hoy
                                                </span>
                                            )}
                                            {m.menu.season_tag && (
                                                <span className="bg-thunderbird-100 text-thunderbird-800 text-[10px] uppercase tracking-wider font-black px-2 py-0.5 rounded">
                                                    {m.menu.season_tag}
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-3">
                                            {Boolean(m.menu.parsed_json?.MenuBreadIncluded) && (
                                                <span className="bg-orange-100 text-orange-800 text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full shadow-sm">
                                                    🍞 Pan
                                                </span>
                                            )}
                                            {Boolean(m.menu.parsed_json?.MenuDrinkIncluded) && (
                                                <span className="bg-blue-100 text-blue-800 text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full shadow-sm">
                                                    🥤 Bebida
                                                </span>
                                            )}
                                            {Boolean(m.menu.parsed_json?.MenuDessertIncluded) && (
                                                <span className="bg-pink-100 text-pink-800 text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full shadow-sm">
                                                    🍮 Postre
                                                </span>
                                            )}
                                            {/* Reuse Button */}
                                            <button
                                                onClick={() => handleReuse(m)}
                                                disabled={savingId === m.menu.id}
                                                className="ml-4 text-[10px] uppercase tracking-wider font-black bg-ecruwhite border-2 border-thunderbird-700 text-thunderbird-700 hover:bg-white px-4 py-2 rounded-lg transition-all cursor-pointer shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                            >
                                                {savingId === m.menu.id ? (
                                                    <>
                                                        <span className="w-3 h-3 border-2 border-thunderbird-700 border-t-transparent rounded-full animate-spin"></span>
                                                        Guardando...
                                                    </>
                                                ) : "Reutilizar para hoy"}
                                            </button>
                                        </div>
                                    </div>
                                    <div className="p-6">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-4">
                                            {/* Primeros */}
                                            <div>
                                                <h3 className="text-[10px] font-black text-thunderbird-600 uppercase tracking-widest mb-3">Primeros platos</h3>
                                                <ul className="space-y-2">
                                                    {m.menu_items
                                                        .filter(item => {
                                                            // Parse item name if it's a JSON string (Point 6 fix)
                                                            let course = "primero";
                                                            try {
                                                                if (item.name.startsWith('{')) {
                                                                    const parsed = JSON.parse(item.name);
                                                                    course = parsed.course;
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
                                                                <li key={item.id} className="text-sm text-black font-medium bg-thunderbird-50/45 rounded-md px-3 py-2 shadow-sm">
                                                                    {String(displayName)}
                                                                </li>
                                                            );
                                                        })}
                                                </ul>
                                            </div>
                                            {/* Segundos */}
                                            <div>
                                                <h3 className="text-[10px] font-black text-thunderbird-600 uppercase tracking-widest mb-3">Segundos platos</h3>
                                                <ul className="space-y-2">
                                                    {m.menu_items
                                                        .filter(item => {
                                                            let course = "segundo";
                                                            try {
                                                                if (item.name.startsWith('{')) {
                                                                    const parsed = JSON.parse(item.name);
                                                                    course = parsed.course;
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
                                                                <li key={item.id} className="text-sm text-black font-medium bg-thunderbird-50/45 rounded-md px-3 py-2 shadow-sm">
                                                                    {String(displayName)}
                                                                </li>
                                                            );
                                                        })}
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </main>
        </ProtectedRoute>
    );
}
