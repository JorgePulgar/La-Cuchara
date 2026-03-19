import Navbar from "@/components/layout/Navbar";
import LoginForm from "@/components/auth/LoginForm";

// Login page — Task 5.1
export default function LoginPage() {
    return (
        <>
            <Navbar />
            <main className="min-h-screen flex items-center justify-center px-4 py-12 bg-ecruwhite">
                <div className="w-full max-w-md">
                    <div className="app-card bg-ecruwhite/80 rounded-2xl shadow-xl border-4 border-white/50 p-8 backdrop-blur-sm">
                        <h1 className="text-2xl font-bold text-center text-gray-900 mb-6">
                            Iniciar sesión
                        </h1>
                        <LoginForm />
                    </div>
                </div>
            </main>
        </>
    );
}
