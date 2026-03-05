import Navbar from "@/components/layout/Navbar";
import Link from "next/link";

export default function HomePage() {
    return (
        <>
            <Navbar />
            <main className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
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
                            className="px-6 py-3 bg-amber-600 hover:bg-amber-700 text-white font-medium rounded-lg transition-colors text-center"
                        >
                            Iniciar sesión
                        </Link>
                        <Link
                            href="/signup"
                            className="px-6 py-3 bg-white hover:bg-gray-100 text-gray-800 font-medium rounded-lg border border-gray-300 transition-colors text-center"
                        >
                            Crear cuenta
                        </Link>
                    </div>

                    <div className="mt-12 bg-amber-50 border border-amber-200 rounded-lg p-5 text-left">
                        <p className="font-semibold text-amber-800 mb-1">🔮 Próximamente</p>
                        <p className="text-amber-700 text-sm">
                            Búsqueda por ubicación, filtros por tipo de comida, menús del día
                            y predicciones con inteligencia artificial.
                        </p>
                    </div>
                </div>
            </main>
        </>
    );
}
