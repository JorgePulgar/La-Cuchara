import Navbar from "@/components/layout/Navbar";
import SignupForm from "@/components/auth/SignupForm";

// Signup page — Task 5.2
export default function SignupPage() {
    return (
        <>
            <Navbar />
            <main className="min-h-screen flex items-center justify-center px-4 py-12 bg-gray-50">
                <div className="w-full max-w-md">
                    <div className="bg-white rounded-2xl shadow-lg p-8">
                        <h1 className="text-2xl font-bold text-center text-gray-900 mb-6">
                            Crear cuenta
                        </h1>
                        <SignupForm />
                    </div>
                </div>
            </main>
        </>
    );
}
