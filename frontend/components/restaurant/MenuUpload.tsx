"use client";

/**
 * frontend/components/restaurant/MenuUpload.tsx
 * Menu upload form: date, image file, season tag.
 * Integrates with Azure Content Understanding for menu analysis.
 * Displays extracted fields, descriptions, and detected items.
 */

import { useState, useEffect, type FormEvent, type ChangeEvent } from "react";
import {
    analyzeMenuImage,
    saveMenu,
    type ImageAnalysisResponse,
} from "@/lib/api";

type AzureFieldValue = {
    type?: string;
    valueString?: string;
    valueNumber?: number;
    valueInteger?: number;
    valueBoolean?: boolean;
    valueArray?: AzureFieldValue[];
    confidence?: number;
};

type EditableMenuField = {
    key: string;
    label: string;
    value: string;
    confidence?: number;
};

type EditableMenuItem = {
    id: string;
    value: string;
    confidence?: number;
    course: "primero" | "segundo";
};

type UploadPhase = "idle" | "analyzing" | "ready";

function getTodayISODate(): string {
    const now = new Date();
    const offset = now.getTimezoneOffset();
    const localDate = new Date(now.getTime() - offset * 60 * 1000);
    return localDate.toISOString().slice(0, 10);
}

function getCurrentSeason(dateStr?: string): string {
    // If dateStr is YYYY-MM-DD, parsing it as new Date(dateStr) might use UTC.
    // We want local month.
    let d: Date;
    if (dateStr) {
        const [y, m, d_num] = dateStr.split('-').map(Number);
        d = new Date(y, m - 1, d_num);
    } else {
        d = new Date();
    }

    const month = d.getMonth(); // 0-indexed: 0=Jan, 1=Feb, 2=Mar...
    if (month >= 2 && month <= 4) return "Primavera"; // Mar, Apr, May
    if (month >= 5 && month <= 7) return "Verano";    // Jun, Jul, Aug
    if (month >= 8 && month <= 10) return "Otoño";   // Sep, Oct, Nov
    return "Invierno"; // Dec, Jan, Feb
}

function prettifyFieldName(fieldName: string): string {
    return fieldName
        .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
        .replace(/_/g, " ")
        .trim();
}

function capitalizeOCRText(value: string): string {
    // Normalize spacing and apply title case for better initial UX in editable inputs.
    return value
        .trim()
        .replace(/\s+/g, " ")
        .toLocaleLowerCase("es-ES")
        .replace(/(^|\s|[-(/])\p{L}/gu, (match) => match.toLocaleUpperCase("es-ES"));
}

function normalizeArrayValue(items: AzureFieldValue[] | undefined): string {
    if (!items || items.length === 0) return "";

    return items
        .map((item) => {
            if (item.valueString !== undefined) return capitalizeOCRText(item.valueString);
            if (item.valueNumber !== undefined) return String(item.valueNumber);
            if (item.valueInteger !== undefined) return String(item.valueInteger);
            if (item.valueBoolean !== undefined) {
                return item.valueBoolean ? "true" : "false";
            }
            return "";
        })
        .filter(Boolean)
        .join("\n");
}

function normalizeFieldValue(field: AzureFieldValue): string {
    if (field.type === "number" && field.valueNumber !== undefined) {
        return String(field.valueNumber);
    }

    if (field.type === "integer" && field.valueInteger !== undefined) {
        return String(field.valueInteger);
    }

    if (field.type === "boolean" && field.valueBoolean !== undefined) {
        return field.valueBoolean ? "true" : "false";
    }

    if (field.type === "array") {
        return normalizeArrayValue(field.valueArray);
    }

    return field.valueString ? capitalizeOCRText(field.valueString) : "";
}

const MENU_ITEM_FIELD_NAMES = new Set(["MenuItems", "MenuItemsFirsts", "MenuItemsSeconds"]);

function buildEditableFields(fields: Record<string, unknown>): EditableMenuField[] {
    return Object.entries(fields)
        .filter(([key]) => !MENU_ITEM_FIELD_NAMES.has(key))
        .map(([key, rawField]) => {
            const azureField = rawField as AzureFieldValue;

            return {
                key,
                label: prettifyFieldName(key),
                value: normalizeFieldValue(azureField),
                confidence: azureField.confidence,
            };
        });
}

function buildEditableMenuItems(fields: Record<string, unknown>): EditableMenuItem[] {
    const items: EditableMenuItem[] = [];
    let index = 0;

    // Helper to extract items from a field array with a given course
    const extractFromField = (
        fieldName: string,
        course: "primero" | "segundo",
    ) => {
        const raw = fields[fieldName] as AzureFieldValue | undefined;
        const values = raw?.valueArray ?? [];

        for (const item of values) {
            const value =
                (item.valueString ? capitalizeOCRText(item.valueString) : undefined) ??
                (item.valueNumber !== undefined ? String(item.valueNumber) : "");

            items.push({
                id: `menu-item-${index}`,
                value,
                confidence: item.confidence,
                course,
            });
            index += 1;
        }
    };

    // Read from the separated fields (Azure La_Cuchara_V2 format)
    extractFromField("MenuItemsFirsts", "primero");
    extractFromField("MenuItemsSeconds", "segundo");

    // Fallback: also check the old generic "MenuItems" field
    if (items.length === 0) {
        extractFromField("MenuItems", "primero");
    }

    return items;
}

let nextManualItemId = 0;

export default function MenuUpload() {
    const [menuDate, setMenuDate] = useState(getTodayISODate());
    const [imageFile, setImageFile] = useState<File | null>(null);
    const [seasonTag, setSeasonTag] = useState(getCurrentSeason());
    const [phase, setPhase] = useState<UploadPhase>("idle");
    const [success, setSuccess] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [error, setError] = useState("");
    const [saving, setSaving] = useState(false);
    const [analysisResult, setAnalysisResult] =
        useState<ImageAnalysisResponse | null>(null);
    const [editableFields, setEditableFields] = useState<EditableMenuField[]>([]);
    const [editableMenuItems, setEditableMenuItems] = useState<EditableMenuItem[]>([]);

    // Auto-select season when date changes (Phase 12 requirement)
    useEffect(() => {
        setSeasonTag(getCurrentSeason(menuDate));
    }, [menuDate]);

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setImageFile(e.target.files[0]);
        }
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError("");
        setSuccess(false);
        setSaveSuccess(false);
        setAnalysisResult(null);
        setEditableFields([]);
        setEditableMenuItems([]);

        if (!imageFile) {
            setError("Debes seleccionar una imagen del menú");
            return;
        }

        setPhase("analyzing");

        try {
            // Send image to backend for Azure Content Understanding analysis
            const result = await analyzeMenuImage(imageFile);

            setAnalysisResult(result);
            setEditableFields(buildEditableFields(result.fields));
            setEditableMenuItems(buildEditableMenuItems(result.fields));
            setMenuDate(getTodayISODate());
            setSuccess(true);
            setPhase("ready");

            // Reset upload input only
            setImageFile(null);

            // Reset file input
            const fileInput = document.getElementById(
                "upload-image"
            ) as HTMLInputElement;
            if (fileInput) fileInput.value = "";
        } catch (err) {
            setPhase("idle");
            setError(
                err instanceof Error
                    ? err.message
                    : "Error al analizar la imagen del menú"
            );
        }
    };

    const handleSaveChanges = async () => {
        setError("");
        setSaveSuccess(false);

        const payloadFields = editableFields.reduce<Record<string, unknown>>(
            (accumulator, field) => {
                accumulator[field.key] = field.value.trim();
                return accumulator;
            },
            {}
        );

        const payloadItems = editableMenuItems
            .filter((item) => item.value.trim())
            .map((item) => JSON.stringify({
                name: item.value.trim(),
                course: item.course,
            }));

        setSaving(true);

        try {
            await saveMenu({
                date: menuDate,
                season_tag: seasonTag.trim() || null,
                fields: payloadFields,
                items: payloadItems,
            });
            setSaveSuccess(true);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Error al guardar el menú corregido"
            );
        } finally {
            setSaving(false);
        }
    };

    const handleAnalyzeAnotherImage = () => {
        setPhase("idle");
        setSuccess(false);
        setSaveSuccess(false);
        setError("");
        setAnalysisResult(null);
        setEditableFields([]);
        setEditableMenuItems([]);
    };

    if (phase === "analyzing") {
        return (
            <div className="w-full max-w-4xl">
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-8 text-center space-y-4">
                    <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-amber-200 border-t-amber-600" />
                    <h3 className="text-lg font-semibold text-amber-900">
                        Analizando imagen del menú
                    </h3>
                    <p className="text-sm text-amber-800">
                        Enviando a Azure Content Understanding y esperando resultados...
                    </p>
                </div>
            </div>
        );
    }

    if (phase === "ready" && analysisResult) {
        return (
            <div className="w-full max-w-4xl space-y-6">
                {success && (
                    <div className="bg-green-50 text-green-700 text-sm px-4 py-3 rounded-lg border border-green-200">
                        ✅ Imagen analizada con éxito
                    </div>
                )}

                {saveSuccess && (
                    <div className="bg-emerald-50 text-emerald-700 text-sm px-4 py-3 rounded-lg border border-emerald-200">
                        ✅ Cambios guardados correctamente en la base de datos
                    </div>
                )}

                {error && (
                    <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg border border-red-200">
                        ❌ {error}
                    </div>
                )}

                <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
                    <div className="border-b pb-4">
                        <h2 className="text-2xl font-bold text-gray-900">
                            Formulario del menú
                        </h2>
                        <p className="text-sm text-gray-600 mt-1">
                            Revisa y corrige los campos antes de guardar.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label
                                htmlFor="menu-date"
                                className="block text-sm font-medium text-gray-700 mb-1"
                            >
                                Fecha del menú
                            </label>
                            <input
                                id="menu-date"
                                type="date"
                                value={menuDate}
                                onChange={(e) => setMenuDate(e.target.value)}
                                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                            />
                        </div>

                        <div>
                            <label
                                htmlFor="season-tag"
                                className="block text-sm font-medium text-gray-700 mb-1"
                            >
                                Temporada
                            </label>
                            <select
                                id="season-tag"
                                value={seasonTag}
                                onChange={(e) => setSeasonTag(e.target.value)}
                                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                            >
                                <option value="">Seleccionar temporada</option>
                                <option value="Primavera">Primavera</option>
                                <option value="Verano">Verano</option>
                                <option value="Otoño">Otoño</option>
                                <option value="Invierno">Invierno</option>
                            </select>
                        </div>
                    </div>

                    {editableFields.length > 0 && (
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-900">
                                Campos del menú
                            </h3>

                            <div className="grid grid-cols-1 gap-4">
                                {editableFields.map((field, index) => (
                                    <div
                                        key={field.key}
                                        className="border border-gray-200 rounded-lg p-4 bg-gray-50"
                                    >
                                        <div className="flex items-center justify-between mb-2">
                                            <label
                                                htmlFor={`field-${field.key}`}
                                                className="text-sm font-medium text-gray-800"
                                            >
                                                {field.label}
                                            </label>
                                            {typeof field.confidence === "number" && (
                                                <span className="text-xs font-semibold px-2 py-1 rounded-full bg-amber-100 text-amber-700">
                                                    {(field.confidence * 100).toFixed(1)}%
                                                </span>
                                            )}
                                        </div>

                                        <input
                                            id={`field-${field.key}`}
                                            type="text"
                                            value={field.value}
                                            onChange={(e) => {
                                                const next = [...editableFields];
                                                next[index] = {
                                                    ...next[index],
                                                    value: e.target.value,
                                                };
                                                setEditableFields(next);
                                            }}
                                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                                        />
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900">
                                    Items del menú
                                </h3>
                                <p className="text-sm text-gray-600">
                                    Cada plato se puede corregir individualmente.
                                </p>
                            </div>
                            <button
                                type="button"
                                onClick={() => {
                                    nextManualItemId += 1;
                                    setEditableMenuItems([
                                        ...editableMenuItems,
                                        {
                                            id: `manual-item-${nextManualItemId}`,
                                            value: "",
                                            course: "primero",
                                        },
                                    ]);
                                }}
                                className="text-sm bg-amber-100 hover:bg-amber-200 text-amber-800 font-medium px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                            >
                                + Añadir plato
                            </button>
                        </div>

                        <div className="space-y-3">
                            {editableMenuItems.map((item, index) => (
                                <div
                                    key={item.id}
                                    className="border border-gray-200 rounded-lg p-4 bg-gray-50"
                                >
                                    <div className="flex items-center justify-between mb-2">
                                        <label
                                            htmlFor={`menu-item-${index}`}
                                            className="text-sm font-medium text-gray-800"
                                        >
                                            Plato {index + 1}
                                        </label>
                                        <div className="flex items-center gap-2">
                                            {typeof item.confidence === "number" && (
                                                <span className="text-xs font-semibold px-2 py-1 rounded-full bg-blue-100 text-blue-700">
                                                    {(item.confidence * 100).toFixed(1)}%
                                                </span>
                                            )}
                                            <button
                                                type="button"
                                                onClick={() => {
                                                    setEditableMenuItems(
                                                        editableMenuItems.filter((_, i) => i !== index)
                                                    );
                                                }}
                                                className="text-red-400 hover:text-red-600 text-lg cursor-pointer px-1"
                                                title="Eliminar plato"
                                            >
                                                ✕
                                            </button>
                                        </div>
                                    </div>

                                    <div className="flex gap-3">
                                        <input
                                            id={`menu-item-${index}`}
                                            type="text"
                                            value={item.value}
                                            onChange={(e) => {
                                                const next = [...editableMenuItems];
                                                next[index] = {
                                                    ...next[index],
                                                    value: e.target.value,
                                                };
                                                setEditableMenuItems(next);
                                            }}
                                            placeholder="Nombre del plato"
                                            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                                        />
                                        <select
                                            value={item.course}
                                            onChange={(e) => {
                                                const next = [...editableMenuItems];
                                                next[index] = {
                                                    ...next[index],
                                                    course: e.target.value as "primero" | "segundo",
                                                };
                                                setEditableMenuItems(next);
                                            }}
                                            className="w-32 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                                        >
                                            <option value="primero">Primero</option>
                                            <option value="segundo">Segundo</option>
                                        </select>
                                    </div>
                                </div>
                            ))}

                            {editableMenuItems.length === 0 && (
                                <div className="text-center py-6 text-gray-400 text-sm">
                                    No hay platos. Pulsa &quot;+ Añadir plato&quot; para empezar.
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="pt-2">
                        <div className="flex flex-col md:flex-row gap-3">
                            <button
                                type="button"
                                onClick={handleSaveChanges}
                                disabled={saving}
                                className="w-full md:w-auto bg-amber-600 hover:bg-amber-700 disabled:bg-amber-400 text-white font-medium py-2.5 px-4 rounded-lg transition-colors cursor-pointer disabled:cursor-not-allowed"
                            >
                                {saving ? "Guardando cambios..." : "Guardar cambios"}
                            </button>

                            <button
                                type="button"
                                onClick={handleAnalyzeAnotherImage}
                                disabled={saving}
                                className="w-full md:w-auto bg-slate-100 hover:bg-slate-200 disabled:bg-slate-100 text-slate-800 font-medium py-2.5 px-4 rounded-lg transition-colors cursor-pointer disabled:cursor-not-allowed"
                            >
                                Analizar otra imagen
                            </button>
                        </div>
                    </div>

                    {editableFields.length === 0 &&
                        editableMenuItems.length === 0 &&
                        (!analysisResult.fields ||
                            Object.keys(analysisResult.fields).length === 0) && (
                            <div className="bg-yellow-50 text-yellow-700 text-sm px-4 py-3 rounded-lg border border-yellow-200">
                                ⚠️ Análisis completado pero no se encontraron elementos
                                estructurados. Verifica la calidad de la imagen.
                            </div>
                        )}
                </div>
            </div>
        );
    }

    return (
        <div className="w-full max-w-4xl space-y-6">
            {error && (
                <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg border border-red-200">
                    ❌ {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
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
                    />
                    {imageFile && (
                        <p className="text-xs text-gray-500 mt-1">
                            Archivo: {imageFile.name} ({(imageFile.size / 1024).toFixed(2)} KB)
                        </p>
                    )}
                </div>

                <button
                    type="submit"
                    className="w-full bg-amber-600 hover:bg-amber-700 text-white font-medium py-2.5 rounded-lg transition-colors cursor-pointer"
                >
                    📸 Analizar menú
                </button>
            </form>
        </div>
    );
}
