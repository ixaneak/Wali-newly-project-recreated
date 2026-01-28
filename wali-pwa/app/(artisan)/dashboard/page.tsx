'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { policyService } from '@/lib/api-client';
import { formatCurrency } from '@/lib/utils';

interface Policy {
    id: string;
    policy_number: string;
    coverage_type: string;
    status: string;
    monthly_premium: number;
    created_at: string;
}

export default function DashboardPage() {
    const router = useRouter();
    const [userId, setUserId] = useState('');
    const [policies, setPolicies] = useState<Policy[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const storedUserId = localStorage.getItem('user_id');
        const phone = localStorage.getItem('user_phone');

        if (!storedUserId || !phone) {
            router.push('/login');
            return;
        }

        setUserId(storedUserId);
        loadPolicies(storedUserId);
    }, [router]);

    const loadPolicies = async (uid: string) => {
        try {
            const response = await policyService.getUserPolicies(uid);
            setPolicies(response.data || []);
        } catch (error) {
            console.error('Failed to load policies:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_id');
        localStorage.removeItem('user_phone');
        router.push('/login');
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active': return 'bg-green-100 text-green-800';
            case 'pending': return 'bg-yellow-100 text-yellow-800';
            case 'cancelled': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center">
                        <h1 className="text-2xl font-bold text-green-600">Wali - Tableau de Bord</h1>
                        <button
                            onClick={handleLogout}
                            className="text-sm text-gray-600 hover:text-gray-800"
                        >
                            Déconnexion
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-gray-600 text-sm mb-2">Polices actives</h3>
                        <p className="text-3xl font-bold text-green-600">
                            {policies.filter(p => p.status === 'active').length}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-gray-600 text-sm mb-2">Total des primes</h3>
                        <p className="text-3xl font-bold text-green-600">
                            {formatCurrency(policies.reduce((sum, p) => sum + p.monthly_premium, 0))}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-gray-600 text-sm mb-2">Réclamations</h3>
                        <p className="text-3xl font-bold text-blue-600">0</p>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <button
                        onClick={() => router.push('/policies/new')}
                        className="bg-green-600 text-white rounded-lg p-6 text-left hover:bg-green-700 transition"
                    >
                        <h3 className="text-xl font-bold mb-2">📋 Nouvelle police</h3>
                        <p className="text-green-100">Souscrire une assurance santé, équipement ou vol</p>
                    </button>
                    <button
                        onClick={() => router.push('/claims/new')}
                        className="bg-blue-600 text-white rounded-lg p-6 text-left hover:bg-blue-700 transition"
                    >
                        <h3 className="text-xl font-bold mb-2">🏥 Déposer une réclamation</h3>
                        <p className="text-blue-100">Soumettre une demande de remboursement</p>
                    </button>
                </div>

                {/* Policies List */}
                <div className="bg-white rounded-lg shadow">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <h2 className="text-xl font-bold text-gray-800">Mes Polices</h2>
                    </div>

                    {loading ? (
                        <div className="px-6 py-12 text-center">
                            <p className="text-gray-500">Chargement...</p>
                        </div>
                    ) : policies.length === 0 ? (
                        <div className="px-6 py-12 text-center">
                            <p className="text-gray-500 mb-4">Aucune police trouvée</p>
                            <button
                                onClick={() => router.push('/policies/new')}
                                className="text-green-600 hover:text-green-700 font-medium"
                            >
                                Souscrire une nouvelle police
                            </button>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-200">
                            {policies.map((policy) => (
                                <div key={policy.id} className="px-6 py-4 hover:bg-gray-50">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="font-semibold text-gray-800">{policy.policy_number}</h3>
                                            <p className="text-sm text-gray-600 capitalize">{policy.coverage_type}</p>
                                        </div>
                                        <div className="text-right">
                                            <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(policy.status)}`}>
                                                {policy.status}
                                            </span>
                                            <p className="text-sm font-semibold text-gray-800 mt-2">
                                                {formatCurrency(policy.monthly_premium)}/mois
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
