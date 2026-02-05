'use client';

import { useRouter } from 'next/navigation';

export default function AdminLoginPage() {
    const router = useRouter();

    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();
        // Simple admin auth - in production, use proper authentication
        localStorage.setItem('admin_token', 'admin-temp-token');
        localStorage.setItem('user_role', 'admin');
        router.push('/admin/claims-review');
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-green-600 to-green-800 flex items-center justify-center px-4">
            <div className="max-w-md w-full bg-white rounded-lg shadow-xl p-8">
                <h1 className="text-3xl font-bold text-gray-800 mb-2">Admin Wali</h1>
                <p className="text-gray-600 mb-8">Connexion administrateur</p>

                <form onSubmit={handleLogin} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Email
                        </label>
                        <input
                            type="email"
                            placeholder="admin@wali.ci"
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Mot de passe
                        </label>
                        <input
                            type="password"
                            placeholder="••••••••"
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        className="w-full bg-green-600 text-white py-3 rounded-lg font-medium hover:bg-green-700 transition"
                    >
                        Se connecter
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <a href="/" className="text-sm text-green-600 hover:text-green-700">
                        ← Retour à l'accueil
                    </a>
                </div>
            </div>
        </div>
    );
}
