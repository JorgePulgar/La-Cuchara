import Navbar from "@/components/layout/Navbar";
import Link from "next/link";

export default function HomePage() {
    return (
        <>
            <Navbar />
            <main className="min-h-screen bg-ecruwhite flex flex-col items-center justify-center px-4">
                <div className="text-center max-w-xl">
                    <h1 className="text-5xl font-bold text-gray-900 mb-4">
                        🍽️ La Cuchara
                    </h1>
                    <p className="text-lg text-gray-600 mb-8">
                        Encuentra restaurantes cercanos y explora sus menús
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <Link
                            href="/login"
                            className="px-6 py-3 bg-thunderbird-700 hover:bg-thunderbird-800 text-ecruwhite font-medium rounded-lg transition-colors text-center"
                        >
                            Iniciar sesión
                        </Link>
                        <Link
                            href="/signup"
                            className="px-6 py-3 bg-ecruwhite/80 hover:bg-white text-gray-800 font-bold rounded-xl border-2 border-thunderbird-100 transition-all text-center shadow-sm"
                        >
                            Crear cuenta
                        </Link>
                    </div>

                    <div className="mt-12 bg-thunderbird-50 border border-thunderbird-200 rounded-lg p-5 text-left">
                        <p className="font-semibold text-thunderbird-800 mb-1">🔮 Próximamente</p>
                        <p className="text-thunderbird-700 text-sm">
                            Búsqueda por ubicación, filtros por tipo de comida, menús del día
                            y predicciones con inteligencia artificial.
                        </p>
                    </div>
                </div>
            </main>
        </>
    );
}
