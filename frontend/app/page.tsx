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
                            className="px-8 py-3 bg-thunderbird-700 hover:bg-thunderbird-800 text-ecruwhite font-bold rounded-xl shadow-lg transition-all text-center uppercase tracking-widest text-sm"
                        >
                            Iniciar sesión
                        </Link>
                        <Link
                            href="/signup"
                            className="px-8 py-3 bg-thunderbird-800 hover:bg-thunderbird-900 text-ecruwhite font-bold rounded-xl shadow-lg transition-all text-center uppercase tracking-widest text-sm border border-thunderbird-600"
                        >
                            Crear cuenta
                        </Link>
                    </div>

                </div>
            </main>
        </>
    );
}
