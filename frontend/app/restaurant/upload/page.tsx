"use client";

// Restaurant menu upload page — Task 6.2
// Protected (role: owner). Uses ProtectedRoute.

import Navbar from "@/components/layout/Navbar";
import ProtectedRoute from "@/components/layout/ProtectedRoute";
import MenuUpload from "@/components/restaurant/MenuUpload";

export default function UploadPage() {
    return (
        <ProtectedRoute requiredRole="owner">
            <Navbar />
            <main className="min-h-screen bg-ecruwhite px-4 py-12">
                <div className="max-w-lg mx-auto">
                    <div className="app-card bg-ecruwhite/80 rounded-2xl shadow-xl border-4 border-white/50 p-8 backdrop-blur-sm">
                        <h1 className="text-2xl font-bold text-gray-900 mb-2">
                            Subir menú
                        </h1>
                        <p className="text-gray-600 mb-6 text-sm">
                            Sube la imagen de tu menú del día o de la semana.
                        </p>
                        <MenuUpload />
                    </div>
                </div>
            </main>
        </ProtectedRoute>
    );
}
